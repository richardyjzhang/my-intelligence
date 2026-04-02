import logging
import os
import sys
import threading
import time
from datetime import datetime

from flask import Flask, Response, jsonify, request

import config
from services import redis_service, mineru_service, es_service, chroma_service
from services.agents.chat import router as chat_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/chat/stream", methods=["POST"])
def chat_stream():
    body = request.get_json(silent=True) or {}
    query = body.get("query", "").strip()
    logger.info("收到 chat 请求: query=%s, history长度=%s", query[:100] if query else "", len(body.get("history", [])))

    if not query:
        logger.warning("chat 请求缺少 query")
        return jsonify({"error": "query is required"}), 400
    if len(query) > 2000:
        logger.warning("chat 请求 query 过长: %s", len(query))
        return jsonify({"error": "query too long (max 2000)"}), 400

    history = body.get("history", [])
    model = body.get("model")
    mode = body.get("mode")

    def generate():
        logger.info("开始生成 SSE 流: model=%s, mode=%s", model or config.CHAT_MODEL, mode)
        event_count = 0
        try:
            for event in chat_agent.chat_stream(query, history, model, mode):
                event_count += 1
                yield event
            logger.info("SSE 流结束, 共发送 %s 个事件", event_count)
        except Exception as e:
            logger.error("SSE 生成器异常: %s", e, exc_info=True)

    return Response(generate(), content_type="text/event-stream")


def consume_delete_queue():
    """消费删除队列，清理文档在 ES 和 ChromaDB 中的数据"""
    count = 0
    while True:
        task = redis_service.pop_delete_task()
        if task is None:
            break

        document_id = task["documentId"]
        logger.info("处理删除任务 documentId=%s", document_id)

        try:
            es_service.delete_document(document_id)
        except Exception as e:
            logger.warning("ES 删除失败(可忽略): documentId=%s, error=%s", document_id, e)

        try:
            chroma_service.delete_document(document_id)
        except Exception as e:
            logger.warning("ChromaDB 删除失败(可忽略): documentId=%s, error=%s", document_id, e)

        count += 1

    if count > 0:
        logger.info("删除任务完成: 共清理 %s 个文档", count)


def phase1_consume_parse_queue():
    """阶段1：消费解析队列，批量取完所有任务并提交给 MinerU"""
    count = 0
    while True:
        task = redis_service.pop_parse_task()
        if task is None:
            break

        document_id = task["documentId"]
        file_path = task["filePath"]
        logger.info("阶段1: 处理解析任务 documentId=%s", document_id)

        try:
            es_service.delete_document(document_id)
            chroma_service.delete_document(document_id)
        except Exception as e:
            logger.warning("清理旧数据时出错(可忽略): documentId=%s, error=%s", document_id, e)

        file_name = task.get("fileName", "")
        task_id = mineru_service.submit_task(file_path, file_name)
        if task_id is None:
            redis_service.push_status(document_id, -1, "MinerU任务提交失败",
                                      error_detail="文件不存在或MinerU服务不可用")
            continue

        task_info = {
            "taskId": task_id,
            "filePath": file_path,
            "title": task.get("title", ""),
            "tags": task.get("tags", []),
            "fileName": task.get("fileName", ""),
            "submittedAt": datetime.now().isoformat(),
        }
        redis_service.save_mineru_task(document_id, task_info)
        count += 1

    if count > 0:
        logger.info("阶段1完成: 共提交 %s 个任务", count)


def phase2_poll_mineru_results():
    """阶段2：轮询 MinerU 任务结果"""
    tasks = redis_service.get_all_mineru_tasks()
    if not tasks:
        return

    logger.info("阶段2: 检查 %s 个 MinerU 任务", len(tasks))

    for doc_id_str, info in tasks.items():
        document_id = int(doc_id_str)
        task_id = info["taskId"]

        status = mineru_service.get_task_status(task_id)
        state = status.get("state", "unknown")

        if state == "done":
            logger.info("MinerU 任务完成: documentId=%s, batchId=%s", document_id, task_id)

            full_zip_url = status.get("full_zip_url", "")
            content = mineru_service.get_task_result(full_zip_url)
            if content is None:
                redis_service.push_status(document_id, -1, "获取MinerU结果失败",
                                          error_detail="任务已完成但获取结果失败")
                redis_service.remove_mineru_task(document_id)
                continue

            redis_service.push_status(document_id, 2, "OCR识别完成")

            index_task = {
                "documentId": document_id,
                "title": info.get("title", ""),
                "content": content,
                "tags": info.get("tags", []),
                "fileName": info.get("fileName", ""),
            }
            redis_service.push_index_task(index_task)
            redis_service.remove_mineru_task(document_id)

        elif state == "failed":
            error_msg = status.get("error", "未知错误")
            logger.error("MinerU 任务失败: documentId=%s, error=%s", document_id, error_msg)
            redis_service.push_status(document_id, -1, "OCR识别失败", error_detail=error_msg)
            redis_service.remove_mineru_task(document_id)

        else:
            logger.debug("MinerU 任务进行中: documentId=%s, state=%s", document_id, state)


def phase3_consume_index_queue():
    """阶段3：消费索引队列，每轮只处理1个"""
    item = redis_service.pop_index_task()
    if item is None:
        return

    document_id = item["documentId"]
    title = item.get("title", "")
    content = item.get("content", "")
    tags = item.get("tags", [])
    file_name = item.get("fileName", "")

    logger.info("阶段3: 索引文档 documentId=%s, title=%s", document_id, title)

    try:
        text_dir = os.path.join(config.FILE_ROOT_PATH, "documents", "texts")
        os.makedirs(text_dir, exist_ok=True)
        text_path = os.path.join(text_dir, f"{document_id}.md")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("纯文本已保存: %s", text_path)
    except Exception as e:
        logger.warning("保存纯文本失败(不影响索引): documentId=%s, error=%s", document_id, e)

    try:
        es_service.index_document(document_id, title, content, tags, file_name)
    except Exception as e:
        logger.error("ES 索引失败: documentId=%s, error=%s", document_id, e)
        redis_service.push_status(document_id, -1, "ES索引写入失败", error_detail=str(e))
        return

    try:
        chroma_service.store_document(document_id, title, content, tags)
    except Exception as e:
        logger.error("ChromaDB 写入失败: documentId=%s, error=%s", document_id, e)
        redis_service.push_status(document_id, -1, "向量化存储失败", error_detail=str(e))
        return

    redis_service.push_status(document_id, 3, "处理完成")
    logger.info("阶段3完成: documentId=%s 已索引并向量化", document_id)


def poll_loop():
    """后台轮询线程"""
    logger.info("文档解析轮询线程启动")
    logger.info("轮询间隔: %ss", config.POLL_INTERVAL)
    logger.info("MinerU 模型: %s", config.MINERU_MODEL_VERSION)
    logger.info("ES: %s", config.ES_HOST)
    logger.info("ChromaDB: %s", config.CHROMA_PERSIST_DIR)

    es_service.check_index()

    while True:
        try:
            consume_delete_queue()
            phase1_consume_parse_queue()
            phase2_poll_mineru_results()
            phase3_consume_index_queue()
        except Exception as e:
            logger.error("轮询异常: %s", e, exc_info=True)

        time.sleep(config.POLL_INTERVAL)


if __name__ == "__main__":
    poll_thread = threading.Thread(target=poll_loop, daemon=True)
    poll_thread.start()

    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=False)
