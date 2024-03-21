import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor

from notetool.secret import get_md5_str
from requests import Session
from requests.adapters import HTTPAdapter
from tqdm import tqdm

import m3u8

logger = logging.getLogger("name")
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:72.0) Gecko/20100101 Firefox/72.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


def get_session(pool_connections, pool_maxsize, max_retries) -> Session:
    """构造session"""
    session = Session()
    adapter = HTTPAdapter(pool_connections=pool_connections, pool_maxsize=pool_maxsize, max_retries=max_retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def get_ts_filename(url):
    file_name = url.split('/')[-1].split('?')[0] + '-' + url.split('?')[1].split('&')[0].split('=')[1]
    return file_name


a = str(uuid.uuid4()).replace("-", "")


class FileMeta:
    def __init__(self, url=None, file_dir="", file_name=None):
        self.url = url
        self.file_name = file_name or get_md5_str(url)
        self.file_dir = file_dir or './cache/'

        self.exit_flag = 0

        self.ts_path = os.path.join(self.file_dir, get_md5_str(url))
        self.ts_list = []
        self.key = ""
        self.load_progress = None

        self.count_complete = 0
        self.count_total = 0
        self.meta = None

        if file_dir and not os.path.isdir(file_dir):
            os.makedirs(file_dir)

        if self.ts_path and not os.path.isdir(self.ts_path):
            os.makedirs(self.ts_path)

        self.init_data()

    def load_done(self):
        pass

    def init_data(self):
        self.meta = m3u8.load(self.url)
        for seg in self.meta.segments:
            self.ts_list.append(seg.absolute_uri)
        self.count_total = len(self.ts_list)
        self.load_progress = tqdm(total=len(self.ts_list))

    def load_update(self, size=1):
        self.load_progress.update(size)

    def merge_file(self, file_dir=None, overwrite=True):
        """
        将TS文件整合在一起
        """
        self.count_complete = 0
        file_dir = file_dir or self.file_dir
        file_output = os.path.join(file_dir, self.file_name + '.mp4')

        with open(file_output, 'wb') as outfile:
            for ts_file in tqdm(self.ts_list, desc=f'{self.file_name}'):
                file_name = get_ts_filename(ts_file)
                file_input = os.path.join(self.ts_path, file_name)

                if not os.path.exists(file_input):
                    continue

                with open(file_input, 'rb') as infile:
                    outfile.write(infile.read())

                # 删除临时ts文件
                os.remove(file_input)
        os.rmdir(self.ts_path)


class M3u8Downloader:
    def __init__(self, session=None, thread_size=64):
        self.thread_size = thread_size
        self.session = session or get_session(30, 30, 3)
        self.thread_pool = ThreadPoolExecutor(max_workers=thread_size, thread_name_prefix="download_")

    def download_thead(self, file: FileMeta, ts_index):
        url = file.ts_list[ts_index]
        file_name = get_ts_filename(url)
        file_path = os.path.join(file.ts_path, file_name)
        if os.path.exists(file_path):
            file.load_update()
            return

        for i in range(5, -1, -1):
            try:
                r = self.session.get(url, timeout=20, headers=headers)
                if not r.ok:
                    continue

                with open(file_path, 'wb') as f:
                    f.write(r.content)
                    file.load_update()
                    break
            except Exception as e:
                logger.info(e)
                pass
            if i == 0:
                print('[FAIL]%s' % url)

    def download(self, file: FileMeta):
        for i in range(0, len(file.ts_list)):
            self.thread_pool.submit(self.download_thead, file, i)

    def wait_shutdown(self):
        self.thread_pool.shutdown(wait=True)

