import os
import datetime


# 存储一个文件，返回相对路径
def store_file(file):
    now = datetime.datetime.now()
    folder = f"data/{now.strftime('%Y%m')}"
    timestamp = now.strftime('%d%H%M%S')
    os.makedirs(folder, exist_ok=True)
    path = f'{folder}/{timestamp}-{file.filename}'
    file.save(path)

    return path


# 删除一个文件
def del_file(rel_path):
    if os.path.exists(rel_path):
        os.remove(rel_path)
