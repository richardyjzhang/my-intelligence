import threading
import redis
import json
import time

from .. import config

r = redis.Redis(host=config['redis-host'],
                port=config['redis-port'],
                password=config['redis-password'],
                decode_responses=True,
                encoding='utf-8')

# 文档处理的队列名
queue_name = 'my-intelligence-extraction'


# 对一个文档进行处理（丢入队列）
def handle_one_doc(id: int, path: str):
    payload = {
        "id": id,
        "path": path,
    }
    payload = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    print(payload)
    r.rpush(queue_name, payload)


# 不断消费队列，处理文档
def start_consuming():
    while True:
        item = r.blpop(queue_name, timeout=0)
        if item:
            data = json.loads(item[1])
            print(data)
            # 模拟处理
            time.sleep(30)


# 开启线程处理文档
def init_dispatcher():
    thread = threading.Thread(target=start_consuming)
    thread.daemon = True
    thread.start()
