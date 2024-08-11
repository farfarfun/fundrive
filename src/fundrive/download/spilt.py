# -*- coding: utf-8 -*-
import os
import os.path

import requests
from .core import Downloader
from .work import WorkerFactory, Worker
from funfile.compress.utils import file_tqdm_bar


class SpiltDownloader(Downloader):
    def __init__(self, blocks_num=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blocks_num = blocks_num or self.filesize // (100 * 1024 * 1024)

        if not self.check_available():
            print(f"{self.filename} this url not support range requests,set blocks_num=1.")
            self.blocks_num = 1

    def __get_range(self):
        size = int(self.filesize) // self.blocks_num
        range_list = []
        for i in range(self.blocks_num):
            start = i * size

            if i == self.blocks_num - 1:
                end = self.filesize - 1
            else:
                end = start + size
            if i > 0:
                start += 1
            range_list.append((start, end))
        return range_list

    def download(self, worker_num=5, capacity=100, prefix="", overwrite=False, *args, **kwargs):
        if not overwrite and os.path.exists(self.filepath) and self.filesize == os.path.getsize(self.filepath):
            return False

        prefix = prefix if prefix is not None and len(prefix) > 0 else ""

        range_list = self.__get_range()

        cache_dir = f"{self.filepath}.cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        success_files = []
        pbar = file_tqdm_bar(path=self.filepath, total=self.filesize, prefix=f"{prefix}|0/{self.blocks_num}|")

        def update_pbar(total, curser, current):
            pbar.update(current)
            pbar.refresh()

        with WorkerFactory(worker_num=worker_num, capacity=capacity, timeout=1) as pool:
            for index, (start, end) in enumerate(range_list):
                tmp_file = f"{cache_dir}/split-{str(index).zfill(5)}.tmp"
                success_file = f"{tmp_file}.success"

                def finish_callback(worker: Worker, *args, **kwargs):
                    dst = f"{worker.filepath}.success"
                    os.rename(worker.filepath, dst)
                    success_files.append(dst)
                    pbar.set_description(
                        desc=f"{prefix}|{len(success_files)}/{self.blocks_num}|{os.path.basename(self.filepath)}"
                    )

                worker = Worker(
                    url=self.url,
                    range_start=start,
                    range_end=end,
                    filepath=tmp_file,
                    update_callback=update_pbar,
                    finish_callback=finish_callback,
                )
                if os.path.exists(success_file) and os.path.getsize(success_file) == worker.size:
                    finish_callback(worker)
                    pbar.update(worker.size)
                    pbar.refresh()
                    continue
                pool.submit(worker=worker)

        assert len(success_files) == self.blocks_num
        with open(self.filepath, "wb") as fw:
            for file in success_files:
                with open(file, "rb") as fr:
                    fw.write(fr.read())
                    fw.flush()
                os.remove(file)
            os.removedirs(cache_dir)

    def check_available(self) -> bool:
        header = {"Range": f"bytes=0-100"}
        with requests.get(self.url, stream=True, headers=header) as req:
            return req.status_code == 206


def download(url, filepath, overwrite=False, worker_num=5, capacity=100, prefix=""):
    SpiltDownloader(url=url, filepath=filepath, overwrite=overwrite).download(
        worker_num=worker_num, capacity=capacity, prefix=prefix
    )
