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


def ensure_index():
    """确保索引存在，不存在则创建"""
    client = get_client()
    if client.indices.exists(index=INDEX_NAME):
        return

    mapping = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        },
        "mappings": {
            "properties": {
                "documentId": {"type": "long"},
                "title": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_smart",
                },
                "content": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_smart",
                },
                "tags": {"type": "keyword"},
                "fileName": {"type": "keyword"},
            }
        },
    }

    client.indices.create(index=INDEX_NAME, body=mapping)
    logger.info("ES 索引 '%s' 已创建", INDEX_NAME)


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
