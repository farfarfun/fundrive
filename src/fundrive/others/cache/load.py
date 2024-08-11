import os.path

import requests

cache_root = os.path.join(os.environ['HOME'], 'notecache')


def url_to_path(url: str):
    if url.startswith("https://raw.githubusercontent.com/notechats"):
        base_url = url.split("https://raw.githubusercontent.com/")[1]
        base_path, filename = os.path.split(base_url)
        cache_path = os.path.join(cache_root, base_path)
        file_path = os.path.join(cache_path, filename)

        # 如果缓存路径不存在则创建
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)

        return file_path
    return None


def load_url_to_cache(url: str, overwrite=False) -> str:
    file_path = url_to_path(url)
    if file_path is None:
        return file_path

    # 如果文件已存在
    if os.path.exists(file_path):
        # 如果不覆盖就返回，覆盖就删除原文件
        if not overwrite:
            return file_path
        else:
            os.remove(file_path)

    with open(file_path, 'wb') as f:
        content = requests.get(url).content
        f.write(content)
    return file_path


def load_from_cache(url: str):
    file_path = load_url_to_cache(url)
    return open(file_path).read()
