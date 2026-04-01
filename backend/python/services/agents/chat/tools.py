"""
对话智能体工具集 —— ChromaDB 检索、消息构建等。
"""

import logging

from services.chroma_service import get_collection, get_embeddings

logger = logging.getLogger(__name__)


def retrieve_context(query: str, top_k: int = 5) -> list[dict]:
    """从 ChromaDB 检索与问题相关的文档片段"""
    try:
        collection = get_collection()
        query_embedding = get_embeddings([query])[0]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        contexts = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else None
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


def build_user_content(query: str, contexts: list[dict]) -> str:
    """构建带知识片段上下文的用户消息内容"""
    if not contexts:
        return query

    snippets = []
    for i, ctx in enumerate(contexts, 1):
        title = ctx.get("title", "未知文档")
        snippets.append(f"【片段{i}】来源：{title}\n{ctx['content']}")
    context_text = "\n\n".join(snippets)
    return f"以下是相关知识片段：\n\n{context_text}\n\n用户问题：{query}"


def build_messages(query: str, contexts: list[dict], history: list[dict]) -> list[dict]:
    """构建 Anthropic Messages API 格式的消息列表（不含 system）"""
    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": build_user_content(query, contexts)})
    return messages
