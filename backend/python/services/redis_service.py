import json
import logging
from typing import Optional

import redis

import config

logger = logging.getLogger(__name__)

PARSE_QUEUE = "doc:parse:queue"           # Java -> Python: 待解析文档任务
DELETE_QUEUE = "doc:delete:queue"         # Java -> Python: 待删除文档任务
MINERU_TASKS_HASH = "doc:mineru:tasks"    # Python 内部: MinerU 异步任务跟踪
INDEX_QUEUE = "doc:index:queue"           # Python 内部: OCR 完成待索引队列
STATUS_QUEUE = "doc:status:queue"         # Python -> Java: 状态回调通知

_client: Optional[redis.Redis] = None


def get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            password=config.REDIS_PASSWORD,
            db=config.REDIS_DB,
            decode_responses=True,
        )
    return _client


def pop_parse_task() -> Optional[dict]:
    data = get_client().rpop(PARSE_QUEUE)
    if data is None:
        return None
    return json.loads(data)


def pop_delete_task() -> Optional[dict]:
    data = get_client().rpop(DELETE_QUEUE)
    if data is None:
        return None
    return json.loads(data)


def save_mineru_task(document_id: int, task_info: dict):
    get_client().hset(MINERU_TASKS_HASH, str(document_id), json.dumps(task_info))


def get_all_mineru_tasks() -> dict[str, dict]:
    raw = get_client().hgetall(MINERU_TASKS_HASH)
    return {doc_id: json.loads(info) for doc_id, info in raw.items()}


def remove_mineru_task(document_id: int):
    get_client().hdel(MINERU_TASKS_HASH, str(document_id))


def push_index_task(task: dict):
    get_client().lpush(INDEX_QUEUE, json.dumps(task, ensure_ascii=False))


def pop_index_task() -> Optional[dict]:
    data = get_client().rpop(INDEX_QUEUE)
    if data is None:
        return None
    return json.loads(data)


def push_status(document_id: int, status: int, message: str,
                error_detail: Optional[str] = None):
    msg = {
        "documentId": document_id,
        "status": status,
        "message": message,
    }
    if error_detail is not None:
        msg["errorDetail"] = error_detail
    get_client().lpush(STATUS_QUEUE, json.dumps(msg, ensure_ascii=False))
    logger.info("状态推送: documentId=%s, status=%s, message=%s", document_id, status, message)
