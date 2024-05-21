import os
import datetime


# 存储一个文件，返回相对路径
def store_file(file):
    now = datetime.datetime.now()
    folder = now.strftime('%Y%m')
    timestamp = now.strftime('%d%H%M%S')
    os.makedirs(folder, exist_ok=True)
    path = f'{folder}/{timestamp}-{file.filename}'
    file.save(path)

    return path
