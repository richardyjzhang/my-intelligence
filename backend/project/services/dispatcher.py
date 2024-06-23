import threading
import redis
import json

import pymupdf
import numpy as np
from paddleocr import PaddleOCR

from elasticsearch import Elasticsearch

from .. import config

# Redis连接
r = redis.Redis(host=config['redis-host'],
                port=config['redis-port'],
                password=config['redis-password'],
                decode_responses=True,
                encoding='utf-8')

# 文档处理的队列名
QUEUE_NAME = 'my-intelligence-extraction'

# OCR实例
ocr = PaddleOCR(use_angle_cls=True, lang='ch')

# ElasticSearch连接
es = Elasticsearch(hosts=config['es-hosts'])

# ElasticSearch Index
ES_INDEX = 'my-intelligence'


# 对一个文档进行处理（丢入队列）
def handle_one_doc(id: int, path: str):
    payload = {
        "id": id,
        "path": path,
    }
    payload = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    r.rpush(QUEUE_NAME, payload)


# 不断消费队列，处理文档
def start_consuming():
    while True:
        item = r.blpop(QUEUE_NAME, timeout=0)
        if item:
            try:
                data = json.loads(item[1])
                content_text = get_doc_content(data["path"])
                es.index(index=ES_INDEX, body={
                    "id": data['id'],
                    "content": content_text,
                })
            except Exception as e:
                print(e)


# 处理一份文档
def get_doc_content(path: str):
    if path.lower().endswith('.pdf'):
        return get_doc_content_pdf(path)


# 处理一份PDF文档
def get_doc_content_pdf(path: str):
    # 将PDF中各业形成图像，并依次调用OCR
    doc = pymupdf.open(path)
    doc_text = ''
    for page in doc:
        pix = page.get_pixmap()
        bytes = np.frombuffer(pix.samples, dtype=np.uint8)
        img = bytes.reshape(pix.height, pix.width, pix.n)
        results_one_page = ocr_one_image(img)
        # 对一页中的各识别结果进行拼装，形成一页的总体文字
        page_text = ''
        for idx in range(len(results_one_page)):
            res = results_one_page[idx]
            # 累加各行文字
            result_text = ''
            for line in res:
                line_text = line[1][0]
                result_text = result_text + line_text
            page_text = page_text + result_text
        doc_text = doc_text + page_text
    return doc_text


# 通过OCR识别一张照片
def ocr_one_image(img):
    results = ocr.ocr(img)
    return results


# 开启线程处理文档
def init_dispatcher():
    thread = threading.Thread(target=start_consuming)
    thread.daemon = True
    thread.start()
