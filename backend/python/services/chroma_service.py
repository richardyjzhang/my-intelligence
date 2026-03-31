import logging
import re

import chromadb
from openai import OpenAI

import config

logger = logging.getLogger(__name__)

COLLECTION_NAME = "documents"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

_chroma_client: chromadb.ClientAPI | None = None
_openai_client: OpenAI | None = None


def get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
    return _chroma_client


def get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(
            base_url=config.OLLAMA_BASE_URL,
            api_key="ollama",
        )
    return _openai_client


def get_collection():
    return get_chroma_client().get_or_create_collection(name=COLLECTION_NAME)


def split_text(text: str) -> list[str]:
    """按段落分块，每块约 CHUNK_SIZE 字，重叠 CHUNK_OVERLAP 字"""
    paragraphs = re.split(r"\n{2,}", text.strip())

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) <= CHUNK_SIZE:
            current_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if len(para) > CHUNK_SIZE:
                for i in range(0, len(para), CHUNK_SIZE - CHUNK_OVERLAP):
                    chunks.append(para[i:i + CHUNK_SIZE])
            else:
                overlap_text = current_chunk[-(CHUNK_OVERLAP):] if current_chunk else ""
                current_chunk = f"{overlap_text}\n\n{para}" if overlap_text else para
                continue
            current_chunk = ""

    if current_chunk:
        chunks.append(current_chunk)

    return chunks if chunks else [text[:CHUNK_SIZE]] if text else []


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """通过 OpenAI 兼容协议调用 Ollama 获取 embeddings"""
    client = get_openai_client()
    resp = client.embeddings.create(
        model=config.EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in resp.data]


def store_document(document_id: int, title: str, content: str,
                   tags: list[str]):
    """分块、向量化并存入 ChromaDB"""
    collection = get_collection()

    delete_document(document_id)

    chunks = split_text(content)
    if not chunks:
        logger.warning("文档内容为空，跳过向量化: documentId=%s", document_id)
        return

    ids = [f"{document_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "documentId": document_id,
            "chunkIndex": i,
            "title": title,
            "tags": ",".join(tags),
        }
        for i in range(len(chunks))
    ]

    embeddings = get_embeddings(chunks)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )
    logger.info("ChromaDB 文档已存储: documentId=%s, chunks=%s", document_id, len(chunks))


def delete_document(document_id: int):
    """删除文档的所有 chunks"""
    collection = get_collection()
    try:
        existing = collection.get(where={"documentId": document_id})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
            logger.info("ChromaDB 已删除旧数据: documentId=%s, count=%s",
                        document_id, len(existing["ids"]))
    except Exception as e:
        logger.warning("ChromaDB 删除失败: documentId=%s, error=%s", document_id, e)
