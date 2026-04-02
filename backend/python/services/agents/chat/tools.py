"""
对话智能体工具集 —— ChromaDB 检索、消息构建等。
"""

import logging
from collections import defaultdict

from services.chroma_service import get_collection, get_embeddings

logger = logging.getLogger(__name__)

EXPAND_WINDOW = 3


def retrieve_context(
    query: str,
    top_k: int = 5,
    max_distance: float = 1.2,
    document_id: int | None = None,
) -> list[dict]:
    """从 ChromaDB 检索与问题相关的文档片段；距离超过阈值则视为不相关。

    指定 document_id 时仅在对应文档的 chunk 内检索，不混入其他文档。
    """
    try:
        collection = get_collection()
        query_embedding = get_embeddings([query])[0]
        q_kw: dict = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if document_id is not None:
            q_kw["where"] = {"documentId": document_id}
        results = collection.query(**q_kw)

        contexts = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                distance = results["distances"][0][i] if results["distances"] else None
                if distance is not None and distance > max_distance:
                    continue
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                contexts.append({
                    "content": doc,
                    "title": meta.get("title", ""),
                    "documentId": meta.get("documentId"),
                    "chunkIndex": meta.get("chunkIndex"),
                    "distance": distance,
                })
        return contexts
    except Exception as e:
        logger.warning("ChromaDB 检索失败: %s", e)
        return []


def _merge_intervals(indices: list[int], window: int) -> list[tuple[int, int]]:
    """将命中的 chunkIndex 列表按扩展窗口合并为连续区间 [(lo, hi), ...]。"""
    if not indices:
        return []
    sorted_idx = sorted(set(indices))
    intervals: list[tuple[int, int]] = []
    lo = max(sorted_idx[0] - window, 0)
    hi = sorted_idx[0] + window
    for idx in sorted_idx[1:]:
        new_lo = max(idx - window, 0)
        new_hi = idx + window
        if new_lo <= hi + 1:
            hi = max(hi, new_hi)
        else:
            intervals.append((lo, hi))
            lo, hi = new_lo, new_hi
    intervals.append((lo, hi))
    return intervals


def retrieve_context_expanded(
    query: str,
    top_k: int = 5,
    max_distance: float = 1.2,
    window: int = EXPAND_WINDOW,
    document_id: int | None = None,
) -> list[dict]:
    """
    向量检索命中片段后，自动扩展同文档的前后相邻 chunk，
    返回文档级上下文列表（每篇文档一个条目，content 为拼接后的连续文本）。
    同时按 documentId 去重。

    指定 document_id 时，检索与扩展均仅限该文档。
    """
    hits = retrieve_context(query, top_k, max_distance, document_id=document_id)
    if not hits:
        return []

    doc_hits: dict[int, dict] = defaultdict(lambda: {"title": "", "indices": []})
    doc_order: list[int] = []
    for h in hits:
        raw_id = h.get("documentId")
        if raw_id is None:
            continue
        try:
            doc_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        if doc_id not in doc_hits:
            doc_order.append(doc_id)
        entry = doc_hits[doc_id]
        entry["title"] = entry["title"] or h.get("title", "")
        chunk_idx = h.get("chunkIndex")
        if chunk_idx is not None:
            entry["indices"].append(int(chunk_idx))

    collection = get_collection()
    results: list[dict] = []

    for doc_id in doc_order:
        entry = doc_hits[doc_id]
        if not entry["indices"]:
            continue

        intervals = _merge_intervals(entry["indices"], window)

        try:
            all_chunks = collection.get(
                where={"documentId": doc_id},
                include=["documents", "metadatas"],
            )
        except Exception as e:
            logger.warning("ChromaDB 获取文档 chunks 失败: documentId=%s, error=%s", doc_id, e)
            continue

        chunk_map: dict[int, str] = {}
        if all_chunks and all_chunks["ids"]:
            for j, cid in enumerate(all_chunks["ids"]):
                meta = all_chunks["metadatas"][j] if all_chunks["metadatas"] else {}
                ci = meta.get("chunkIndex")
                if ci is not None:
                    chunk_map[int(ci)] = all_chunks["documents"][j]

        segments: list[str] = []
        for lo, hi in intervals:
            parts = []
            for ci in range(lo, hi + 1):
                if ci in chunk_map:
                    parts.append(chunk_map[ci])
            if parts:
                segments.append("\n\n".join(parts))

        if segments:
            results.append({
                "documentId": doc_id,
                "title": entry["title"],
                "content": "\n\n---\n\n".join(segments),
            })

    return results


def build_user_content(
    query: str,
    contexts: list[dict],
    single_document_id: int | None = None,
) -> str:
    """构建带知识上下文的用户消息内容。"""
    if not contexts:
        return query

    snippets = []
    for i, ctx in enumerate(contexts, 1):
        title = ctx.get("title", "未知文档")
        snippets.append(f"【参考{i}】来源：{title}\n{ctx['content']}")
    context_text = "\n\n---\n\n".join(snippets)
    header = "以下是相关参考资料：\n\n"
    if single_document_id is not None:
        header = (
            "【范围限定】本次问答仅围绕 documentId=%s 的同一篇文档；"
            "下列【参考】均来自该文档。请只依据这些材料作答，不要在回答或引用列表中写出"
            "未出现在下方参考资料中的其他文档名称。\n\n"
        ) % single_document_id
        header += "相关参考资料：\n\n"
    return f"{header}{context_text}\n\n用户问题：{query}"


def build_messages(
    query: str,
    contexts: list[dict],
    history: list[dict],
    single_document_id: int | None = None,
) -> list[dict]:
    """构建 OpenAI Chat API 格式的消息列表（不含 system）"""
    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({
        "role": "user",
        "content": build_user_content(query, contexts, single_document_id=single_document_id),
    })
    return messages
