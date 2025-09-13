#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文叔叔网盘驱动实现

文叔叔是一个免费的临时文件分享服务，支持匿名上传和下载。
本驱动基于文叔叔API实现，支持文件上传、下载和分享功能。

主要功能:
- 匿名文件上传
- 分享链接下载
- 文件管理
- 存储空间查询

作者: FunDrive Team
"""

import base64
import concurrent.futures
import hashlib
import os
import subprocess
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

import orjson
import requests
from funget import simple_download
from funutil import getLogger
from tqdm import tqdm

from fundrive.core import BaseDrive, DriveFile

logger = getLogger("fundrive")


class WSSDrive(BaseDrive):
    """
    文叔叔网盘驱动

    基于文叔叔API实现的临时文件分享驱动，支持匿名上传和下载功能。
    文叔叔是一个免费的临时文件分享服务，无需注册即可使用。
    """

    def __init__(self, **kwargs):
        """
        初始化文叔叔驱动

        Args:
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)

        self.base_url = "https://www.wenshushu.cn"
        self.session = None
        self.token = None

        # 文件存储信息
        self.uploaded_files = {}  # 存储已上传文件的信息

    def login(self, **kwargs) -> bool:
        """
        登录文叔叔（匿名登录）

        Returns:
            登录是否成功
        """
        try:
            logger.info("正在匿名登录文叔叔...")

            self.session = requests.Session()

            # 匿名登录获取token
            response = self.session.post(
                url=f"{self.base_url}/ap/login/anonymous",
                json={"dev_info": "{}"},
                timeout=30,
            )

            if response.status_code != 200:
                logger.error(f"匿名登录失败: {response.status_code}")
                return False

            result = response.json()
            if result.get("code") != 0:
                logger.error(f"匿名登录失败: {result.get('message', '未知错误')}")
                return False

            self.token = result["data"]["token"]

            # 设置请求头
            self.session.headers.update(
                {
                    "X-TOKEN": self.token,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0",
                    "Accept-Language": "en-US, en;q=0.9",
                    "Content-Type": "application/json",
                }
            )

            # 获取用户信息
            self._get_userinfo()

            logger.info("✅ 文叔叔匿名登录成功")
            return True

        except Exception as e:
            logger.error(f"❌ 文叔叔登录失败: {e}")
            return False

    def _get_userinfo(self):
        """获取用户信息"""
        try:
            self.session.post(
                url=f"{self.base_url}/ap/user/userinfo",
                json={"plat": "pcweb"},
                timeout=10,
            )
        except:
            pass

    def get_storage_info(self) -> Dict[str, Any]:
        """
        获取存储空间信息

        Returns:
            存储空间信息
        """
        try:
            response = self.session.post(
                url=f"{self.base_url}/ap/user/storage", json={}, timeout=10
            )

            if response.status_code != 200:
                return {}

            result = response.json()
            if result.get("code") != 0:
                return {}

            data = result["data"]
            rest_space = int(data["rest_space"])
            send_space = int(data["send_space"])
            storage_space = rest_space + send_space

            storage_info = {
                "used_space": send_space,
                "free_space": rest_space,
                "total_space": storage_space,
                "used_space_gb": round(send_space / 1024**3, 2),
                "free_space_gb": round(rest_space / 1024**3, 2),
                "total_space_gb": round(storage_space / 1024**3, 2),
            }

            logger.info(
                f"存储空间: 已用 {storage_info['used_space_gb']}GB, "
                f"剩余 {storage_info['free_space_gb']}GB, "
                f"总计 {storage_info['total_space_gb']}GB"
            )

            return storage_info

        except Exception as e:
            logger.error(f"获取存储信息失败: {e}")
            return {}

    # BaseDrive接口实现
    def exist(self, fid: str, filename: str = None) -> bool:
        """
        检查文件是否存在（文叔叔不支持文件列表，只能检查已上传的文件）

        Args:
            fid: 文件ID或分享链接
            filename: 文件名（可选）

        Returns:
            文件是否存在
        """
        try:
            # 检查是否为已上传的文件
            if fid in self.uploaded_files:
                return True

            # 尝试解析分享链接
            if fid.startswith("http"):
                return self._check_share_url_valid(fid)

            return False

        except Exception as e:
            logger.error(f"检查文件存在性失败: {e}")
            return False

    def _check_share_url_valid(self, share_url: str) -> bool:
        """检查分享链接是否有效"""
        try:
            # 解析分享链接获取token或tid
            if len(share_url.split("/")[-1]) == 16:
                token = share_url.split("/")[-1]
                response = self.session.post(
                    url=f"{self.base_url}/ap/task/token",
                    json={"token": token},
                    timeout=10,
                )
                return response.status_code == 200 and response.json().get("code") == 0
            elif len(share_url.split("/")[-1]) == 11:
                tid = share_url.split("/")[-1]
                response = self.session.post(
                    url=f"{self.base_url}/ap/task/mgrtask",
                    json={"tid": tid, "password": ""},
                    timeout=10,
                )
                return response.status_code == 200 and response.json().get("code") == 0

            return False

        except:
            return False

    def mkdir(self, fid: str, dirname: str) -> bool:
        """
        创建目录（文叔叔不支持目录结构）

        Args:
            fid: 父目录路径
            dirname: 目录名

        Returns:
            创建是否成功
        """
        logger.warning("文叔叔不支持目录结构，无法创建目录")
        return False

    def delete(self, fid: str) -> bool:
        """
        删除文件（文叔叔不支持删除已分享的文件）

        Args:
            fid: 文件ID

        Returns:
            删除是否成功
        """
        logger.warning("文叔叔不支持删除已分享的文件")
        return False

    def get_file_list(self, fid: str = "", *args, **kwargs) -> List[DriveFile]:
        """
        获取文件列表（文叔叔不支持文件列表，返回已上传文件）

        Args:
            fid: 目录路径（忽略）

        Returns:
            文件列表
        """
        try:
            files = []
            for file_id, file_info in self.uploaded_files.items():
                drive_file = DriveFile(
                    fid=file_id,
                    name=file_info.get("name", ""),
                    size=file_info.get("size", 0),
                    ext={
                        "type": "file",
                        "upload_time": file_info.get("upload_time", ""),
                        "share_url": file_info.get("share_url", ""),
                        "mgr_url": file_info.get("mgr_url", ""),
                    },
                )
                files.append(drive_file)

            return files

        except Exception as e:
            logger.error(f"获取文件列表失败: {e}")
            return []

    def get_dir_list(self, fid: str = "", *args, **kwargs) -> List[DriveFile]:
        """
        获取目录列表（文叔叔不支持目录结构）

        Args:
            fid: 目录路径

        Returns:
            目录列表（空）
        """
        logger.info("文叔叔不支持目录结构")
        return []

    def get_file_info(self, fid: str, *args, **kwargs) -> Optional[DriveFile]:
        """
        获取文件信息

        Args:
            fid: 文件ID或分享链接

        Returns:
            文件信息
        """
        try:
            # 检查已上传文件
            if fid in self.uploaded_files:
                file_info = self.uploaded_files[fid]
                return DriveFile(
                    fid=fid,
                    name=file_info.get("name", ""),
                    size=file_info.get("size", 0),
                    ext={
                        "type": "file",
                        "upload_time": file_info.get("upload_time", ""),
                        "share_url": file_info.get("share_url", ""),
                        "mgr_url": file_info.get("mgr_url", ""),
                    },
                )

            # 尝试从分享链接获取信息
            if fid.startswith("http"):
                return self._get_share_file_info(fid)

            return None

        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return None

    def _get_share_file_info(self, share_url: str) -> Optional[DriveFile]:
        """从分享链接获取文件信息"""
        try:
            # 解析链接获取tid
            if len(share_url.split("/")[-1]) == 16:
                token = share_url.split("/")[-1]
                response = self.session.post(
                    url=f"{self.base_url}/ap/task/token",
                    json={"token": token},
                    timeout=10,
                )
                if response.status_code != 200:
                    return None
                tid = response.json()["data"]["tid"]
            elif len(share_url.split("/")[-1]) == 11:
                tid = share_url.split("/")[-1]
            else:
                return None

            # 获取任务信息
            response = self.session.post(
                url=f"{self.base_url}/ap/task/mgrtask",
                json={"tid": tid, "password": ""},
                timeout=10,
            )

            if response.status_code != 200:
                return None

            result = response.json()
            if result.get("code") != 0:
                return None

            data = result["data"]
            file_size = int(data.get("file_size", 0))

            return DriveFile(
                fid=share_url,
                name=f"shared_file_{tid}",
                size=file_size,
                ext={
                    "type": "file",
                    "tid": tid,
                    "expire": data.get("expire", ""),
                    "share_url": share_url,
                },
            )

        except Exception as e:
            logger.error(f"获取分享文件信息失败: {e}")
            return None

    def get_dir_info(self, fid: str, *args, **kwargs) -> Optional[DriveFile]:
        """
        获取目录信息（文叔叔不支持目录结构）

        Args:
            fid: 目录路径

        Returns:
            目录信息（None）
        """
        logger.info("文叔叔不支持目录结构")
        return None

    def upload_file(
        self,
        filepath: str,
        fid: str,
        filename: str = None,
        callback: callable = None,
        **kwargs,
    ) -> bool:
        """
        上传文件到文叔叔

        Args:
            filepath: 本地文件路径
            fid: 目标目录路径（文叔叔忽略此参数）
            filename: 上传后的文件名（可选）
            callback: 进度回调函数

        Returns:
            上传是否成功
        """
        try:
            logger.info(f"正在上传文件: {filepath}")

            if not os.path.exists(filepath):
                logger.error(f"文件不存在: {filepath}")
                return False

            # 创建内部驱动实例用于上传
            internal_drive = _WSSBaseDrive()

            # 创建上传器
            uploader = Uploader(
                file_path=filepath,
                drive=internal_drive,
                chunk_size=kwargs.get("chunk_size", 2097152),
            )

            # 执行上传
            result = uploader.upload(
                max_workers=kwargs.get("max_workers", os.cpu_count())
            )

            if result:
                # 保存上传文件信息
                file_id = f"upload_{int(time.time())}"
                self.uploaded_files[file_id] = {
                    "name": filename or os.path.basename(filepath),
                    "size": os.path.getsize(filepath),
                    "upload_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "local_path": filepath,
                    "share_url": getattr(uploader, "share_url", ""),
                    "mgr_url": getattr(uploader, "mgr_url", ""),
                }

                logger.info(f"✅ 文件上传成功: {filepath}")
                return True
            else:
                logger.error(f"❌ 文件上传失败: {filepath}")
                return False

        except Exception as e:
            logger.error(f"上传文件失败: {e}")
            return False

    def download_file(
        self,
        fid: str,
        filedir: str = ".",
        filename: str = None,
        callback: callable = None,
        **kwargs,
    ) -> bool:
        """
        从文叔叔下载文件

        Args:
            fid: 分享链接URL
            filedir: 下载目录
            filename: 保存的文件名（可选）
            callback: 进度回调函数

        Returns:
            下载是否成功
        """
        try:
            logger.info(f"正在下载文件: {fid}")

            if not fid.startswith("http"):
                logger.error("文叔叔需要分享链接进行下载")
                return False

            # 创建内部驱动实例用于下载
            internal_drive = _WSSBaseDrive()

            # 创建下载器
            downloader = Downloader(
                share_url=fid, drive=internal_drive, cache_dir=filedir
            )

            # 执行下载
            success = downloader.download()

            if success:
                logger.info("✅ 文件下载成功")
                return True
            else:
                logger.error("❌ 文件下载失败")
                return False

        except Exception as e:
            logger.error(f"下载文件失败: {e}")
            return False

    def download_dir(
        self, fid: str, filedir: str = "./cache", overwrite: bool = False, **kwargs
    ) -> bool:
        """
        下载目录（文叔叔不支持目录结构，此方法等同于下载文件）

        Args:
            fid: 分享链接URL
            filedir: 下载目录
            overwrite: 是否覆盖已存在的文件

        Returns:
            下载是否成功
        """
        logger.info("文叔叔不支持目录结构，将尝试作为文件下载")
        return self.download_file(fid, filedir, **kwargs)

    # 高级功能实现
    def search(self, keyword: str, fid: str = "", **kwargs) -> List[DriveFile]:
        """
        搜索文件（在已上传文件中搜索）

        Args:
            keyword: 搜索关键词
            fid: 搜索范围（忽略）

        Returns:
            搜索结果列表
        """
        try:
            logger.info(f"正在搜索文件: {keyword}")

            results = []
            for file_id, file_info in self.uploaded_files.items():
                if keyword.lower() in file_info.get("name", "").lower():
                    drive_file = DriveFile(
                        fid=file_id,
                        name=file_info.get("name", ""),
                        size=file_info.get("size", 0),
                        ext={
                            "type": "file",
                            "upload_time": file_info.get("upload_time", ""),
                            "share_url": file_info.get("share_url", ""),
                            "mgr_url": file_info.get("mgr_url", ""),
                        },
                    )
                    results.append(drive_file)

            logger.info(f"搜索完成，找到 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    def get_quota(self) -> Dict[str, Any]:
        """
        获取存储配额信息

        Returns:
            配额信息
        """
        return self.get_storage_info()


class _WSSBaseDrive:
    """文叔叔内部基础驱动类（保持向后兼容）"""

    def __init__(self, *args, **kwargs):
        self.session = None
        self.login_anonymous()

    def login_anonymous(self):
        self.session = requests.Session()
        r = self.session.post(
            url="https://www.wenshushu.cn/ap/login/anonymous", json={"dev_info": "{}"}
        )
        self.session.headers["X-TOKEN"] = r.json()["data"]["token"]
        self.session.headers["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0"
        )
        self.session.headers["Accept-Language"] = "en-US, en;q=0.9"

    def storage(self):
        r = self.session.post(url="https://www.wenshushu.cn/ap/user/storage", json={})
        rsp = r.json()
        rest_space = int(rsp["data"]["rest_space"])
        send_space = int(rsp["data"]["send_space"])
        storage_space = rest_space + send_space
        logger.info(
            "当前已用空间:{}GB,剩余空间:{}GB,总空间:{}GB".format(
                round(send_space / 1024**3, 2),
                round(rest_space / 1024**3, 2),
                round(storage_space / 1024**3, 2),
            )
        )

    def userinfo(self):
        self.session.post(
            url="https://www.wenshushu.cn/ap/user/userinfo", json={"plat": "pcweb"}
        )


class Uploader:
    def __init__(self, file_path, drive=None, chunk_size=2097152, *args, **kwargs):
        self.drive = drive or _WSSBaseDrive()
        self.session = self.drive.session
        self.chunk_size = chunk_size
        self.file_path = file_path
        self.file_size = os.path.getsize(file_path)
        self.is_part = True if self.file_size > self.chunk_size else False

    def get_epoch_time(self):
        r = self.session.get(
            url="https://www.wenshushu.cn/ag/time",
            headers={
                "Prod": "com.wenshushu.web.pc",
                "Referer": "https://www.wenshushu.cn/",
            },
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
                "count": 1,
            },
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
            url="https://www.wenshushu.cn/ap/uploadv2/psurl", json=payload
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
                json={"processId": up_id},
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
                "location": {"boxid": boxid, "preid": preid},
            },
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
            "file_count": 1,
        }
        # POST的内容在服务端会以字串形式接受然后直接拼接X-TOKEN，不会先反序列化JSON字串再拼接
        # 加密函数中的JSON序列化与此处的JSON序列化的字串形式两者必须完全一致，否则校验失败
        r = self.session.post(
            url="https://www.wenshushu.cn/ap/task/addsend",
            json=req_data,
            headers={
                "A-code": self.get_cipherheader(
                    epochtime, self.session.headers["X-TOKEN"], req_data
                ),
                "Prod": "com.wenshushu.web.pc",
                "Referer": "https://www.wenshushu.cn/",
                "Origin": "https://www.wenshushu.cn",
                "Req-Time": epochtime,
            },
        )
        rsp = r.json()
        if rsp["code"] == 1021:
            raise Exception(f"操作太快啦！请{rsp['message']}秒后重试")

        data = rsp["data"]
        logger.info(f"data: {data}")
        bid, ufileid, tid = data["bid"], data["ufileid"], data["tid"]
        upId = self.get_up_id(bid, ufileid, tid)
        return bid, ufileid, tid, upId

    def copysend(self, boxid, taskid, preid):
        r = self.session.post(
            url="https://www.wenshushu.cn/ap/task/copysend",
            json={"bid": boxid, "tid": taskid, "ufileid": preid},
        )
        rsp = r.json()
        logger.info(f"个人管理链接：{rsp['data']['mgr_url']}")
        logger.info(f"公共链接：{rsp['data']['public_url']}")

    def sha1_str(self, s):
        cm = hashlib.sha1(s.encode()).hexdigest()
        return cm

    def calc_file_hash(self, hash_type, block=None):
        read_size = self.chunk_size if self.is_part else None
        if not block:
            with open(self.file_path, "rb") as f:
                block = f.read(read_size)
        if hash_type == "MD5":
            hash_code = hashlib.md5(block).hexdigest()
        elif hash_type == "SHA1":
            hash_code = hashlib.sha1(block).hexdigest()
        else:
            raise NotImplementedError
        return hash_code

    def get_cipherheader(self, epochtime, token, data):
        try:
            import base58
            from Cryptodome.Cipher import DES
            from Cryptodome.Util import Padding
        except Exception as e:
            logger.info(f"error: {e} traceback: {traceback.format_exc()}")
            subprocess.check_call(["pip", "install", "pycryptodomex"])
            import base58
            from Cryptodome.Cipher import DES
            from Cryptodome.Util import Padding

        # cipherMethod: DES/CBC/PKCS7Padding
        json_dumps = orjson.dumps(data).decode("utf-8")
        md5_hash_code = hashlib.md5((json_dumps + token).encode()).hexdigest()
        base58_hash_code = base58.b58encode(md5_hash_code)
        # 时间戳逆序取5位并作为时间戳字串索引再次取值，最后拼接"000"
        key_iv = (
            "".join([epochtime[int(i)] for i in epochtime[::-1][:5]]) + "000"
        ).encode()
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
            "uf": {"name": name, "boxid": boxid, "preid": preid},
            "upId": upId,
        }

        if not self.is_part:
            payload["hash"]["cm"] = cm  # 把MD5用SHA1加密
        for _ in range(2):
            r = self.session.post(
                url="https://www.wenshushu.cn/ap/uploadv2/fast", json=payload
            )
            rsp = r.json()
            can_fast = rsp["data"]["status"]
            ufile = rsp["data"]["ufile"]
            if can_fast and not ufile:
                hash_codes = ""
                for block, _ in self.read_file():
                    hash_codes += self.calc_file_hash("MD5", block)
                payload["hash"]["cm"] = self.sha1_str(hash_codes)
            elif can_fast and ufile:
                logger.info(f"文件{name}可以被秒传！")
                self.get_process(upId)
                self.copysend(boxid, taskid, preid)

        return name, taskid, boxid, preid, upId

    def upload(self, max_workers=os.cpu_count()):
        try:
            fname, tid, boxid, preid, upId = self.fast()
            pbar = tqdm(
                desc=f"{max_workers}%{fname}",
                total=self.file_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            )
            if self.is_part:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_list = []
                    for i in range(
                        (self.file_size + self.chunk_size - 1) // self.chunk_size
                    ):
                        ul_size = (
                            self.chunk_size
                            if self.chunk_size * (i + 1) <= self.file_size
                            else self.file_size % self.chunk_size
                        )
                        future_list.append(
                            executor.submit(
                                self.file_put,
                                [fname, upId, ul_size, i + 1, pbar],
                                self.file_path,
                                self.chunk_size * i,
                                ul_size,
                            )
                        )
                    concurrent.futures.as_completed(future_list)
            else:
                self.file_put(
                    [fname, upId, self.file_size, pbar],
                    self.file_path,
                    0,
                    self.file_size,
                )

            self.complete(self.is_part, fname, upId, tid, boxid, preid)
            self.get_process(upId)

            # 保存分享链接信息
            self.share_url = f"https://www.wenshushu.cn/f/{tid}"
            self.mgr_url = f"https://www.wenshushu.cn/mgr/{tid}"

            return True

        except Exception as e:
            logger.error(f"上传失败: {e}")
            return False


class Downloader:
    def __init__(self, share_url, drive=None, cache_dir="./", *args, **kwargs):
        self.drive = drive or _WSSBaseDrive()
        self.session = self.drive.session
        self.share_url = share_url
        self.cache_dir = cache_dir

    def get_tid(self, token):
        r = self.session.post(
            url="https://www.wenshushu.cn/ap/task/token", json={"token": token}
        )
        return r.json()["data"]["tid"]

    def mgrtask(self, tid):
        r = self.session.post(
            url="https://www.wenshushu.cn/ap/task/mgrtask",
            json={"tid": tid, "password": ""},
        )
        rsp = r.json()
        expire = rsp["data"]["expire"]
        days, remainder = divmod(int(float(expire)), 3600 * 24)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        logger.info(f"文件过期时间:{days}天{hours}时{minutes}分{seconds}秒")

        file_size = rsp["data"]["file_size"]
        logger.info(f"文件大小:{round(int(file_size) / 1024**2, 2)}MB")
        return rsp["data"]["boxid"], rsp["data"]["ufileid"]  # pid

    def sign_url(self, fid):
        r = self.session.post(
            url="https://www.wenshushu.cn/ap/dl/sign",
            json={"consumeCode": 0, "type": 1, "ufileid": fid},
        )
        if r.json()["data"]["url"] == "" and r.json()["data"]["ttNeed"] != 0:
            raise Exception("对方的分享流量不足")
        return r.json()["data"]["url"]

    def download(self):
        url = self.share_url
        if len(url.split("/")[-1]) == 16:
            token = url.split("/")[-1]
            tid = self.get_tid(token)
        elif len(url.split("/")[-1]) == 11:
            tid = url.split("/")[-1]
        else:
            raise Exception("链接错误")
        bid, pid = self.mgrtask(tid)
        r = self.session.post(
            url="https://www.wenshushu.cn/ap/ufile/list",
            json={
                "start": 0,
                "sort": {"name": "asc"},
                "bid": bid,
                "pid": pid,
                "type": 1,
                "options": {"uploader": "true"},
                "size": 50,
            },
        )
        rsp = r.json()
        success = True
        try:
            for file in rsp["data"]["fileList"]:
                filename = file["fname"]
                url = self.sign_url(file["fid"])
                simple_download(url, filepath=f"{self.cache_dir}/{filename}")
        except Exception as e:
            logger.error(f"下载失败: {e}")
            success = False

        return success


# 向后兼容的别名
WenShuShuDrive = WSSDrive
