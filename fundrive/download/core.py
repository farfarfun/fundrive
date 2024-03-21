# -*- coding: utf-8 -*-
import os

import requests


class Downloader:
    def __init__(self, url, filepath, overwrite=False, filesize=None):
        self.url = url
        self.filepath = filepath
        self.overwrite = overwrite
        self.filesize = filesize or self.__get_size()
        self.filename = os.path.basename(self.filepath)

    def download(self, *args, **kwargs):
        pass

    def __get_size(self):
        with requests.Session() as sess:
            resp = sess.get(self.url, stream=True)
            return int(resp.headers.get("content-length", 0))
