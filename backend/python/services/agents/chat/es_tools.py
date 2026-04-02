"""
Elasticsearch 文档检索（无高亮），供文档查找智能体使用。
"""

import logging

from services.es_service import INDEX_NAME, get_client

logger = logging.getLogger(__name__)


def search_documents(query: str, size: int = 20) -> list[dict]:
    """
    全文检索文档，返回 documentId、title、tags、fileName、score。
    查询结构与 Java SearchServiceImpl.buildDocumentQuery 对齐（无标签过滤）。
    """
    q = (query or "").strip()
    if not q:
        return []

    query_body = {
        "bool": {
            "must": [
                {
                    "bool": {
                        "minimum_should_match": 1,
                        "should": [
                            {"match_phrase": {"title": {"query": q, "boost": 10}}},
                            {
                                "match": {
                                    "title": {
                                        "query": q,
                                        "analyzer": "ik_smart",
                                        "operator": "and",
                                        "boost": 5,
                                    }
                                }
                            },
                            {"match_phrase": {"content": {"query": q, "boost": 2}}},
                            {
                                "match": {
                                    "content": {
                                        "query": q,
                                        "analyzer": "ik_smart",
                                        "operator": "and",
                                        "boost": 1,
                                    }
                                }
                            },
                        ],
                    }
                }
            ]
        }
    }

    try:
        client = get_client()
        resp = client.search(
            index=INDEX_NAME,
            size=size,
            source=["documentId", "title", "tags", "fileName"],
            query=query_body,
        )
    except Exception as e:
        logger.warning("ES 检索失败: %s", e)
        return []

    body = getattr(resp, "body", resp)
    if not isinstance(body, dict):
        body = dict(body) if body else {}
    hits = body.get("hits", {}).get("hits", []) or []
    out: list[dict] = []
    for h in hits:
        src = h.get("_source") or {}
        score = h.get("_score")
        out.append({
            "documentId": src.get("documentId"),
            "title": src.get("title") or "",
            "tags": src.get("tags") or [],
            "fileName": src.get("fileName") or "",
            "score": score,
        })
    return out
