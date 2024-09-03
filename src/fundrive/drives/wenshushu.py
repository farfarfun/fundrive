import base64
import concurrent.futures
import hashlib
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from fundrive.core import DriveSystem
from fundrive.download import simple_download
from tqdm import tqdm


class BaseDrive:
    def __init__(self, *args, **kwargs):
        self.session = None
        self.login_anonymous()

    def login_anonymous(self):
        self.session = requests.Session()
        r = self.session.post(
            url='https://www.wenshushu.cn/ap/login/anonymous',
            json={
                "dev_info": "{}"
            }
        )
        self.session.headers['X-TOKEN'] = r.json()['data']['token']
        self.session.headers[
            'User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0"
        self.session.headers['Accept-Language'] = "en-US, en;q=0.9"

    def storage(self):
        r = self.session.post(
            url='https://www.wenshushu.cn/ap/user/storage',
            json={}
        )
        rsp = r.json()
        rest_space = int(rsp['data']['rest_space'])
        send_space = int(rsp['data']['send_space'])
        storage_space = rest_space + send_space
        print('当前已用空间:{}GB,剩余空间:{}GB,总空间:{}GB'.format(
            round(send_space / 1024 ** 3, 2),
            round(rest_space / 1024 ** 3, 2),
            round(storage_space / 1024 ** 3, 2)
        ))

    def userinfo(self):
        self.session.post(
            url='https://www.wenshushu.cn/ap/user/userinfo',
            json={"plat": "pcweb"}
        )


class Uploader:
    def __init__(self, file_path, drive: BaseDrive=None, chunk_size=2097152, *args, **kwargs):
        self.drive = drive or BaseDrive()
        self.session = drive.session
        self.chunk_size = chunk_size
        self.file_path = file_path
        self.file_size = os.path.getsize(file_path)
        self.is_part = True if self.file_size > self.chunk_size else False

    def get_epoch_time(self):
        r = self.session.get(
            url='https://www.wenshushu.cn/ag/time',
            headers={
                "Prod": "com.wenshushu.web.pc",
                "Referer": "https://www.wenshushu.cn/"
            }
        )
        rsp = r.json()
        return rsp["data"]["time"]

    def get_up_id(self, bid: str, ufileid: str, tid: str):
        r = self.session.post(
            url="https://www.wenshushu.cn/ap/uploadv2/getupid",
            json={
                "preid": ufileid,
                "boxid": bid,
                "linkid": tid,
                "utype": "sendcopy",
                "originUpid": "",
                "length": self.file_size,
                "count": 1
            }
        )
        return r.json()["data"]["upId"]

    def psurl(self, fname, upId, psize, part_num=None, pbar: tqdm = None):
        payload = {
            "ispart": self.is_part,
            "fname": fname,
            "fsize": psize,
            "upId": upId,
        }
        if self.is_part:
            payload["partnu"] = part_num
        r = self.session.post(
            url="https://www.wenshushu.cn/ap/uploadv2/psurl",
            json=payload
        )
        rsp = r.json()
        url = rsp["data"]["url"]
        if pbar:
            pbar.update(psize)
        return url

    def file_put(self, psurl_args, fn, offset=0, read_size=None):
        with open(fn, "rb") as fio:
            fio.seek(offset)
            requests.put(url=self.psurl(*psurl_args), data=fio.read(read_size))

    def get_process(self, up_id: str):
        while True:
            r = self.session.post(
                url="https://www.wenshushu.cn/ap/ufile/getprocess",
                json={
                    "processId": up_id
                }
            )
            if r.json()["data"]["rst"] == "success":
                return True
            time.sleep(1)

    def complete(self, is_part, fname, upId, tid, boxid, preid):
        self.session.post(
            url="https://www.wenshushu.cn/ap/uploadv2/complete",
            json={
                "ispart": is_part,
                "fname": fname,
                "upId": upId,
                "location": {
                    "boxid": boxid,
                    "preid": preid
                }
            }
        )
        self.copysend(boxid, tid, preid)

    def addsend(self):
        self.drive.userinfo()
        self.drive.storage()
        epochtime = self.get_epoch_time()
        req_data = {
            "sender": "",
            "remark": "",
            "isextension": False,
            "notSaveTo": False,
            "notDownload": False,
            "notPreview": False,
            "downPreCountLimit": 0,
            "trafficStatus": 0,
            "pwd": "",
            "expire": "1",
            "recvs": ["social", "public"],
            "file_size": self.file_size,
            "file_count": 1
        }
        # POST的内容在服务端会以字串形式接受然后直接拼接X-TOKEN，不会先反序列化JSON字串再拼接
        # 加密函数中的JSON序列化与此处的JSON序列化的字串形式两者必须完全一致，否则校验失败
        r = self.session.post(
            url='https://www.wenshushu.cn/ap/task/addsend',
            json=req_data,
            headers={
                "A-code": self.get_cipherheader(epochtime, self.session.headers['X-TOKEN'], req_data),
                "Prod": "com.wenshushu.web.pc",
                "Referer": "https://www.wenshushu.cn/",
                "Origin": "https://www.wenshushu.cn",
                "Req-Time": epochtime,
            }
        )
        rsp = r.json()
        if rsp["code"] == 1021:
            raise Exception(f'操作太快啦！请{rsp["message"]}秒后重试')

        data = rsp["data"]
        assert data, "需要滑动验证码"
        bid, ufileid, tid = data["bid"], data["ufileid"], data["tid"]
        upId = self.get_up_id(bid, ufileid, tid)
        return bid, ufileid, tid, upId

    def copysend(self, boxid, taskid, preid):
        r = self.session.post(
            url='https://www.wenshushu.cn/ap/task/copysend',
            json={
                'bid': boxid,
                'tid': taskid,
                'ufileid': preid
            }
        )
        rsp = r.json()
        print(f"个人管理链接：{rsp['data']['mgr_url']}")
        print(f"公共链接：{rsp['data']['public_url']}")

    def sha1_str(self, s):
        cm = hashlib.sha1(s.encode()).hexdigest()
        return cm

    def calc_file_hash(self, hash_type, block=None):
        read_size = self.chunk_size if self.is_part else None
        if not block:
            with open(self.file_path, 'rb') as f:
                block = f.read(read_size)
        if hash_type == "MD5":
            hash_code = hashlib.md5(block).hexdigest()
        elif hash_type == "SHA1":
            hash_code = hashlib.sha1(block).hexdigest()
        return hash_code

    def get_cipherheader(self, epochtime, token, data):
        try:
            from Cryptodome.Cipher import DES
            from Cryptodome.Util import Padding
            import base58
        except Exception as e:
            print(e)
            subprocess.check_call(["pip", "install", "pycryptodomex"])
            from Cryptodome.Cipher import DES
            from Cryptodome.Util import Padding
            import base58

        # cipherMethod: DES/CBC/PKCS7Padding
        json_dumps = json.dumps(data, ensure_ascii=False)
        md5_hash_code = hashlib.md5((json_dumps + token).encode()).hexdigest()
        base58_hash_code = base58.b58encode(md5_hash_code)
        # 时间戳逆序取5位并作为时间戳字串索引再次取值，最后拼接"000"
        key_iv = ("".join([epochtime[int(i)] for i in epochtime[::-1][:5]]) + "000").encode()
        cipher = DES.new(key_iv, DES.MODE_CBC, key_iv)
        cipherText = cipher.encrypt(
            Padding.pad(base58_hash_code, DES.block_size, style="pkcs7")
        )
        return base64.b64encode(cipherText)

    def read_file(self):
        part_num = 0
        with open(self.file_path, "rb") as f:
            while True:
                block = f.read(self.chunk_size)
                part_num += 1
                if block:
                    yield block, part_num
                else:
                    return

    def fast(self):
        boxid, preid, taskid, upId = self.addsend()
        cm1, cs1 = self.calc_file_hash("MD5"), self.calc_file_hash("SHA1")
        cm = self.sha1_str(cm1)
        name = os.path.basename(self.file_path)

        payload = {
            "hash": {
                "cm1": cm1,  # MD5
                "cs1": cs1,  # SHA1
            },
            "uf": {
                "name": name,
                "boxid": boxid,
                "preid": preid
            },
            "upId": upId
        }

        if not self.is_part:
            payload['hash']['cm'] = cm  # 把MD5用SHA1加密
        for _ in range(2):
            r = self.session.post(
                url='https://www.wenshushu.cn/ap/uploadv2/fast',
                json=payload
            )
            rsp = r.json()
            can_fast = rsp["data"]["status"]
            ufile = rsp['data']['ufile']
            if can_fast and not ufile:
                hash_codes = ''
                for block, _ in self.read_file():
                    hash_codes += self.calc_file_hash("MD5", block)
                payload['hash']['cm'] = self.sha1_str(hash_codes)
            elif can_fast and ufile:
                print(f'文件{name}可以被秒传！')
                self.get_process(upId)
                self.copysend(boxid, taskid, preid)

        return name, taskid, boxid, preid, upId

    def upload(self, max_workers=os.cpu_count()):
        fname, tid, boxid, preid, upId = self.fast()
        pbar = tqdm(desc=f"{max_workers}%{fname}", total=self.file_size, unit="B", unit_scale=True, unit_divisor=1024)
        if self.is_part:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_list = []
                for i in range((self.file_size + self.chunk_size - 1) // self.chunk_size):
                    ul_size = self.chunk_size if self.chunk_size * (i + 1) <= self.file_size \
                        else self.file_size % self.chunk_size
                    future_list.append(executor.submit(
                        self.file_put, [fname, upId, ul_size, i + 1, pbar],
                        self.file_path, self.chunk_size * i, ul_size))
                concurrent.futures.as_completed(future_list)
        else:
            self.file_put([fname, upId, self.file_size, pbar], self.file_path, 0, self.file_size)

        self.complete(self.is_part, fname, upId, tid, boxid, preid)
        self.get_process(upId)


class Downloader:
    def __init__(self,  share_url,drive: BaseDrive=None, cache_dir='./', *args, **kwargs):
        self.drive = drive or BaseDrive()
        self.session = drive.session
        self.share_url = share_url
        self.cache_dir = cache_dir
        super().__init__(*args, **kwargs)

    def get_tid(self, token):
        r = self.session.post(
            url='https://www.wenshushu.cn/ap/task/token',
            json={
                'token': token
            }
        )
        return r.json()['data']['tid']

    def mgrtask(self, tid):
        r = self.session.post(
            url='https://www.wenshushu.cn/ap/task/mgrtask',
            json={
                'tid': tid,
                'password': ''
            }
        )
        rsp = r.json()
        expire = rsp['data']['expire']
        days, remainder = divmod(int(float(expire)), 3600 * 24)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f'文件过期时间:{days}天{hours}时{minutes}分{seconds}秒')

        file_size = rsp['data']['file_size']
        print(f'文件大小:{round(int(file_size) / 1024 ** 2, 2)}MB')
        return rsp['data']['boxid'], rsp['data']['ufileid']  # pid

    def sign_url(self, fid):
        r = self.session.post(
            url='https://www.wenshushu.cn/ap/dl/sign',
            json={
                'consumeCode': 0,
                'type': 1,
                'ufileid': fid
            }
        )
        if r.json()['data']['url'] == "" and r.json()['data']['ttNeed'] != 0:
            raise Exception("对方的分享流量不足")
        return r.json()['data']['url']

    def download(self):
        url = self.share_url
        if len(url.split('/')[-1]) == 16:
            token = url.split('/')[-1]
            tid = self.get_tid(token)
        elif len(url.split('/')[-1]) == 11:
            tid = url.split('/')[-1]
        else:
            raise Exception('链接错误')
        bid, pid = self.mgrtask(tid)
        r = self.session.post(
            url='https://www.wenshushu.cn/ap/ufile/list',
            json={
                "start": 0,
                "sort": {
                    "name": "asc"
                },
                "bid": bid,
                "pid": pid,
                "type": 1,
                "options": {
                    "uploader": "true"
                },
                "size": 50
            }
        )
        rsp = r.json()
        for file in rsp['data']['fileList']:
            filename = file['fname']
            url = self.sign_url(file['fid'])
            simple_download(url, filepath=f'{self.cache_dir}/{filename}')


class WSSDrive(DriveSystem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drive = BaseDrive()

    def upload_dir(self, dir_path="./cache", overwrite=False, *args, **kwargs) -> bool:
        pass

    def download_dir(self, dir_path="./cache", overwrite=False, *args, **kwargs) -> bool:
        pass

    def upload_file(self, file_path="./cache", overwrite=False, *args, **kwargs) -> bool:
        uploader = Uploader(drive=self.drive, file_path=file_path)
        try:
            uploader.upload()
        except Exception as e:
            print(e)

    def download_file(self, share_url=None, dir_path="./cache", overwrite=False, *args, **kwargs) -> bool:
        downloader = Downloader(drive=self.drive, share_url=share_url, cache_dir=dir_path)
        try:
            downloader.download()
        except Exception as e:
            print(e)
