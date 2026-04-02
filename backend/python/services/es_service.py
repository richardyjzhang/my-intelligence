import logging

from elasticsearch import Elasticsearch

import config

logger = logging.getLogger(__name__)

INDEX_NAME = "documents"

_client: Elasticsearch | None = None


def get_client() -> Elasticsearch:
    global _client
    if _client is None:
        _client = Elasticsearch(config.ES_HOST)
    return _client


def check_index():
    """检查索引是否存在，不存在则抛出异常"""
    client = get_client()
    if not client.indices.exists(index=INDEX_NAME):
        raise RuntimeError(
            f"ES 索引 '{INDEX_NAME}' 不存在，请先手动创建。"
            f"参考 docs/elasticsearch-design.md 中的创建索引命令。"
        )


def index_document(document_id: int, title: str, content: str,
                   tags: list[str], file_name: str):
    """索引一个文档"""
    client = get_client()
    doc = {
        "documentId": document_id,
        "title": title,
        "content": content,
        "tags": tags,
        "fileName": file_name,
    }
    client.index(index=INDEX_NAME, id=str(document_id), body=doc)
    logger.info("ES 文档已索引: documentId=%s, title=%s", document_id, title)


def delete_document(document_id: int):
    """删除文档索引"""
    client = get_client()
    try:
        client.delete(index=INDEX_NAME, id=str(document_id))
        logger.info("ES 文档已删除: documentId=%s", document_id)
    except Exception as e:
        logger.warning("ES 删除文档失败: documentId=%s, error=%s", document_id, e)


def get_document_content(document_id: int) -> str | None:
    """按 documentId 读取 ES 中的全文 content；不存在或失败时返回 None。"""
    client = get_client()
    try:
        result = client.get(
            index=INDEX_NAME,
            id=str(document_id),
            source_includes=["content"],
        )
        src = result.get("_source") or {}
        content = src.get("content")
        return content if isinstance(content, str) else None
    except Exception as e:
        logger.warning("ES 读取文档正文失败: documentId=%s, error=%s", document_id, e)
        return None
