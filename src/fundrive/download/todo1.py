import os

import requests
from tqdm import tqdm


def download_by_request(url, file_path, size=None, overwrite=False, prefix="") -> bool:
    prefix = f"{prefix}--" if prefix is not None and len(prefix) > 0 else ""
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    if not overwrite and os.path.exists(file_path) and os.path.getsize(file_path) == size:
        return False
    with requests.Session() as sess:
        resp = sess.get(url, stream=True)
        size = size or int(resp.headers.get("content-length", 0))

        if not overwrite and os.path.exists(file_path) and os.path.getsize(file_path) == size:
            return False

        with open(file_path, "wb") as file:
            with tqdm(
                total=size,
                ncols=120,
                desc=f"{prefix}{os.path.basename(file_path)}",
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for data in resp.iter_content(chunk_size=2048):
                    bar.update(file.write(data))
                return True
