# -*- coding: utf-8 -*-
import os

import requests
from .core import Downloader
from tqdm import tqdm


class SimpleDownloader(Downloader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def download(self, prefix="", chunk_size=2048, *args, **kwargs) -> bool:
        prefix = f"{prefix}--" if prefix is not None and len(prefix) > 0 else ""
        if not os.path.exists(os.path.dirname(self.filepath)):
            os.makedirs(os.path.dirname(self.filepath))
        if not self.overwrite and os.path.exists(self.filepath) and os.path.getsize(self.filepath) == self.filesize:
            return False
        with requests.Session() as sess:
            resp = sess.get(self.url, stream=True)

            with open(self.filepath, "wb") as file:
                with tqdm(
                    total=self.filesize,
                    ncols=120,
                    desc=f"{prefix}{os.path.basename(self.filepath)}",
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    for data in resp.iter_content(chunk_size=chunk_size):
                        bar.update(file.write(data))
                    return True


def download(url, filepath, overwrite=False, prefix="", chunk_size=2048):
    SimpleDownloader(url=url, filepath=filepath, overwrite=overwrite).download(prefix=prefix, chunk_size=chunk_size)
