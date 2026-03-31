import io
import logging
import os
import zipfile
from typing import Optional

import httpx

import config

logger = logging.getLogger(__name__)

API_BASE = "https://mineru.net/api/v4"
TIMEOUT = httpx.Timeout(60.0, connect=15.0)


def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.MINERU_TOKEN}",
    }


def submit_task(file_path: str, file_name: str) -> Optional[str]:
    """
    通过批量上传接口提交文件给 MinerU 云端解析。
    返回 batch_id（作为任务跟踪 ID）。
    """
    abs_path = os.path.join(config.FILE_ROOT_PATH, file_path)

    if not os.path.exists(abs_path):
        logger.error("文件不存在: %s", abs_path)
        return None

    try:
        resp = httpx.post(
            f"{API_BASE}/file-urls/batch",
            headers=_headers(),
            json={
                "files": [{"name": file_name}],
                "model_version": config.MINERU_MODEL_VERSION,
                "is_ocr": True,
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        result = resp.json()

        if result.get("code") != 0:
            logger.error("MinerU 申请上传链接失败: %s", result.get("msg"))
            return None

        batch_id = result["data"]["batch_id"]
        file_url = result["data"]["file_urls"][0]

        with open(abs_path, "rb") as f:
            put_resp = httpx.put(file_url, content=f.read(), timeout=TIMEOUT)
            if put_resp.status_code not in (200, 201):
                logger.error("文件上传到 OSS 失败: HTTP %s", put_resp.status_code)
                return None

        logger.info("MinerU 任务已提交: batch_id=%s, file=%s", batch_id, file_name)
        return batch_id

    except Exception as e:
        logger.error("提交 MinerU 任务失败: file=%s, error=%s", file_path, e)
        return None


def get_task_status(batch_id: str) -> dict:
    """
    查询 MinerU 批量任务状态。
    返回 {"state": "done|pending|running|failed|converting", "full_zip_url": "...", ...}
    """
    try:
        resp = httpx.get(
            f"{API_BASE}/extract-results/batch/{batch_id}",
            headers=_headers(),
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        result = resp.json()

        if result.get("code") != 0:
            return {"state": "unknown", "error": result.get("msg", "未知错误")}

        extract_results = result["data"].get("extract_result", [])
        if not extract_results:
            return {"state": "pending"}

        item = extract_results[0]
        return {
            "state": item.get("state", "unknown"),
            "full_zip_url": item.get("full_zip_url", ""),
            "error": item.get("err_msg", ""),
        }

    except Exception as e:
        logger.error("查询 MinerU 任务状态失败: batch_id=%s, error=%s", batch_id, e)
        return {"state": "unknown", "error": str(e)}


def get_task_result(full_zip_url: str) -> Optional[str]:
    """下载结果 zip 并提取 full.md 的内容"""
    try:
        resp = httpx.get(full_zip_url, timeout=httpx.Timeout(120.0, connect=15.0))
        resp.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            for name in zf.namelist():
                if name.endswith("full.md"):
                    return zf.read(name).decode("utf-8")

        logger.warning("zip 中未找到 full.md")
        return None

    except Exception as e:
        logger.error("获取 MinerU 结果失败: url=%s, error=%s", full_zip_url, e)
        return None
