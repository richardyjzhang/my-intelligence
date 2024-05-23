import threading
import redis
import json

from .. import config

r = redis.Redis(host=config['redis-host'],
                port=config['redis-port'],
                password=config['redis-password'],
                decode_responses=True)

# 文档处理的队列名
queue_name = 'my-intelligence-extraction'


# 对一个文档进行处理（丢入队列）
def handle_one_doc(id: int, path: str):
    payload = {
        "id": id,
        "path": path,
    }
    payload = json.dumps(payload)
    print(payload)
    r.rpush(queue_name, payload)


# 不断消费队列，处理文档
def start_consuming():
    while True:
        item = r.blpop(queue_name, timeout=0)
        if item:
            print(item)


# 开启线程处理文档
def init_dispatcher():
    thread = threading.Thread(start_consuming)
    thread.daemon = True
    thread.start()
