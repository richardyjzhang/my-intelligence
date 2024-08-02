import os
import datetime

from . import config


# 存储一个文件，返回相对路径
def store_file(file):
    now = datetime.datetime.now()
    root_folder = config['store-root']
    rel_folder = now.strftime('%Y%m')
    abs_folder = os.path.join(root_folder, rel_folder)
    timestamp = now.strftime('%d%H%M%S')
    os.makedirs(abs_folder, exist_ok=True)
    rel_path = f'{rel_folder}/{timestamp}-{file.filename}'
    abs_path = f'{abs_folder}/{timestamp}-{file.filename}'
    file.save(abs_path)

    return rel_path


# 删除一个文件
def del_file(rel_path):
    root_folder = config['store-root']
    abs_path = os.path.join(root_folder, rel_path)
    if os.path.exists(abs_path):
        os.remove(abs_path)
