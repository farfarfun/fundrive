import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from random import random
from time import sleep
from typing import List

from .utils import *
from funsecret.secret import SecretManage
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from tqdm import tqdm
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

# up_url='https://pc.woozooo.com/fileup.php'
up_url = "http://up.woozooo.com/fileup.php"


def File(
    name="",
    id=0,
    time="",
    size="",
    _type="",
    downs=0,
    has_pwd=0,
    has_des=0,
    type="",
) -> dict:
    return {
        "id": id,
        "name": name,
        "size": size,
        "type": _type or type,
        "time": time,
        "downs": downs,
        "has_pwd": has_pwd,
        "has_des": has_des,
    }


def Folder(name="", id=0, has_pwd=False, desc="") -> dict:
    return {
        "name": name,
        "id": id,
        "has_pwd": has_pwd,
        "desc": desc,
    }


def FolderId(name, id) -> dict:
    return {
        "name": name,
        "id": id,
    }


def rec_file(name, id, _type="", size="", time="", type="") -> dict:
    return {
        "name": name,
        "id": id,
        "type": _type or type,
        "time": time,
        "size": size,
    }


def rec_folder(name, id, size, time, files) -> dict:
    return {
        "name": name,
        "id": id,
        "size": size,
        "time": time,
        "files": files,
    }


def file_detail(
    code=0,
    name="",
    size="",
    _type="",
    time="",
    desc="",
    pwd="",
    url="",
    durl="",
    type="",
) -> dict:
    return {
        "code": code,
        "name": name,
        "size": size,
        "type": _type or type,
        "time": time,
        "desc": desc,
        "pwd": pwd,
        "url": url,
        "durl": durl,
    }


def ShareInfo(
    code=0,
    name="",
    url="",
    pwd="",
    desc="",
) -> dict:
    return {"code": code, "name": name, "url": url, "pwd": pwd, "desc": desc}


def direct_url_info(code, name, durl) -> dict:
    return {"code": code, "name": name, "durl": durl}


def folder_info(name="", id=0, pwd="", time="", desc="", url="") -> dict:
    return {"name": name, "id": id, "time": time, "pwd": pwd, "desc": desc, "url": url}


def file_in_folder(name="", time="", size="", _type="", url="", type="") -> dict:
    return {"name": name, "time": time, "size": size, "type": _type or type, "url": url}


def FolderDetail(code=0, folder=None, files=None) -> dict:
    return {"code": code, "folder": folder, "files": files}


def find_filter(array: list, condition) -> list:
    """筛选出满足条件的 item
    condition(item) -> True
    """
    return [it for it in array if condition(it)]


def find_by_name(array: list, name: str):
    """使用文件名搜索(仅返回首个匹配项)"""
    for item in array:
        if name == item["name"]:
            return item
    return None


def update_by_id(array: list, fid, **kwargs):
    """通过 id 搜索元素并更新"""
    item = find_by_id(array, fid)
    pos = array.index(item)
    array[pos] = array[pos].update(kwargs)


def find_by_id(array: list, fid: int):
    """使用 id 搜索(精确)"""
    for item in array:
        if fid == item["id"]:
            return item
    return None


def pop_by_id(array: list, fid):
    for item in array:
        if item["id"] == fid:
            array.remove(item)
            return item
    return None


class CodeDetail:
    FAILED = -1
    SUCCESS = 0
    ID_ERROR = 1
    PASSWORD_ERROR = 2
    LACK_PASSWORD = 3
    ZIP_ERROR = 4
    MKDIR_ERROR = 5
    URL_INVALID = 6
    FILE_CANCELLED = 7
    PATH_ERROR = 8
    NETWORK_ERROR = 9
    CAPTCHA_ERROR = 10
    OFFICIAL_LIMITED = 11


class LanZouCloud(object):
    def __init__(self):
        self._session = requests.Session()
        self._captcha_handler = None
        self._limit_mode = True  # 是否保持官方限制
        self._timeout = 15  # 每个请求的超时(不包含下载响应体的用时)
        self._max_size = 100  # 单个文件大小上限 MB
        self._upload_delay = (0, 0)  # 文件上传延时
        # self._host_url = 'https://www.lanzous.com'
        self._host_url = "https://pan.lanzoui.com"
        self._doupload_url = "https://pc.woozooo.com/doupload.php"
        self._account_url = "https://pc.woozooo.com/account.php"
        self._mydisk_url = "https://pc.woozooo.com/mydisk.php"
        self._cookies = None
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
            # 'Referer': 'https://www.lanzous.com',
            # 'Referer': 'https://www.lanzoui.com',
            "Referer": "https://pc.woozooo.com/mydisk.php",
            "Accept-Language": "zh-CN,zh;q=0.9",  # 提取直连必需设置这个，否则拿不到数据
        }
        disable_warnings(InsecureRequestWarning)  # 全局禁用 SSL 警告

    def _get(self, url, **kwargs):
        kwargs.setdefault("timeout", self._timeout)
        kwargs.setdefault("headers", self._headers)
        for possiable_url in self.all_possiable_urls(url):
            try:
                return self._session.get(possiable_url, verify=False, **kwargs)
            except (ConnectionError, requests.RequestException):
                logger.warning(f"_get({possiable_url}) failed, try another domain")

        return None

    def _post(self, url, data, **kwargs):
        kwargs.setdefault("timeout", self._timeout)
        kwargs.setdefault("headers", self._headers)
        for possiable_url in self.all_possiable_urls(url):
            try:
                return self._session.post(possiable_url, data, verify=False, **kwargs)
            except (ConnectionError, requests.RequestException):
                logger.warning(
                    f"_post({possiable_url}, {data}) failed, try another domain"
                )

        return None

    def all_possiable_urls(self, lanzouyun_url: str) -> List[str]:
        if self._host_url not in lanzouyun_url:
            return [lanzouyun_url]

        old_domain = "pan.lanzoui"

        base_host_urls = [
            "pan.lanzoux",
            "wws.lanzoux",
            "www.lanzoux",
            "wwx.lanzoux",
            "wws.lanzous",
            "www.lanzous",
            "wwx.lanzous",
            "up.lanzoui",
        ]

        return [
            lanzouyun_url,
            *[lanzouyun_url.replace(old_domain, base) for base in base_host_urls],
        ]

    def ignore_limits(self):
        """解除官方限制"""
        logger.warning(
            "*** You have enabled the big file upload and filename disguise features ***"
        )
        logger.warning(
            "*** This means that you fully understand what may happen and still agree to take the risk ***"
        )
        self._limit_mode = False

    def set_max_size(self, max_size=100) -> int:
        """设置单文件大小限制(会员用户可超过 100M)"""
        if max_size < 100:
            return CodeDetail.FAILED
        self._max_size = max_size
        return CodeDetail.SUCCESS

    def set_upload_delay(self, t_range: tuple) -> int:
        """设置上传大文件数据块时，相邻两次上传之间的延时，减小被封号的可能"""
        if 0 <= t_range[0] <= t_range[1]:
            self._upload_delay = t_range
            return CodeDetail.SUCCESS
        return CodeDetail.FAILED

    def set_captcha_handler(self, captcha_handler):
        """设置下载验证码处理函数
        :param captcha_handler (img_data) -> str 参数为图片二进制数据,需返回验证码字符
        """
        self._captcha_handler = captcha_handler

    def login(self, username, password) -> int:
        """登录蓝奏云控制台"""
        login_data = {
            "action": "login",
            "task": "login",
            "setSessionId": "",
            "setToken": "",
            "setSig": "",
            "setScene": "",
            "username": username,
            "password": password,
        }
        phone_header = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/82.0.4051.0 Mobile Safari/537.36"
        }
        html = self._get(self._account_url)
        if not html:
            return CodeDetail.NETWORK_ERROR
        formhash = re.findall(r'name="formhash" value="(.+?)"', html.text)
        if not formhash:
            return CodeDetail.FAILED
        login_data["formhash"] = formhash[0]
        html = self._post(self._account_url, login_data, headers=phone_header)
        if not html:
            return CodeDetail.NETWORK_ERROR
        if "登录成功" in html.text:
            self._cookies = html.cookies.get_dict()
            return CodeDetail.SUCCESS
        else:
            return CodeDetail.FAILED

    def get_cookie(self) -> dict:
        """获取用户 Cookie"""
        return self._cookies

    def login_by_cookie(
        self, cookie: dict = None, ylogin=None, phpdisk_info=None
    ) -> int:
        """通过cookie登录"""
        secret = SecretManage()
        cookie = cookie or {
            "ylogin": secret.read("drive", "lanzou", "ylogin", value=ylogin),
            "phpdisk_info": secret.read(
                "drive", "lanzou", "phpdisk_info", value=phpdisk_info
            ),
        }

        self._session.cookies.update(cookie)
        html = self._get(self._account_url)
        if not html:
            return CodeDetail.NETWORK_ERROR
        return CodeDetail.FAILED if "网盘用户登录" in html.text else CodeDetail.SUCCESS

    def logout(self) -> int:
        """注销"""
        html = self._get(self._account_url, params={"action": "logout"})
        if not html:
            return CodeDetail.NETWORK_ERROR
        return CodeDetail.SUCCESS if "退出系统成功" in html.text else CodeDetail.FAILED

    def delete(self, fid, is_file=True) -> int:
        """把网盘的文件、无子文件夹的文件夹放到回收站"""
        post_data = (
            {"task": 6, "file_id": fid} if is_file else {"task": 3, "folder_id": fid}
        )
        result = self._post(self._doupload_url, post_data)
        if not result:
            return CodeDetail.NETWORK_ERROR
        return CodeDetail.SUCCESS if result.json()["zt"] == 1 else CodeDetail.FAILED

    def clean_rec(self) -> int:
        """清空回收站"""
        post_data = {"action": "delete_all", "task": "delete_all"}
        html = self._get(
            self._mydisk_url, params={"item": "recycle", "action": "files"}
        )
        if not html:
            return CodeDetail.NETWORK_ERROR
        post_data["formhash"] = re.findall(r'name="formhash" value="(.+?)"', html.text)[
            0
        ]  # 设置表单 hash
        html = self._post(self._mydisk_url + "?item=recycle", post_data)
        if not html:
            return CodeDetail.NETWORK_ERROR
        return (
            CodeDetail.SUCCESS if "清空回收站成功" in html.text else CodeDetail.FAILED
        )

    def get_rec_dir_list(self) -> []:
        """获取回收站文件夹列表"""
        # 回收站中文件(夹)名只能显示前 17 个中文字符或者 34 个英文字符，如果这些字符相同，则在文件(夹)名后添加 (序号) ，以便区分
        html = self._get(
            self._mydisk_url, params={"item": "recycle", "action": "files"}
        )
        if not html:
            return []
        dirs = re.findall(
            r"folder_id=(\d+).+?>&nbsp;(.+?)\.{0,3}</a>.*\n+.*<td.+?>(.+?)</td>.*\n.*<td.+?>(.+?)</td>",
            html.text,
        )
        all_dir_list = []  # 文件夹信息列表
        dir_name_list = []  # 文件夹名列表d
        counter = 1  # 重复计数器
        for fid, name, size, time in dirs:
            if name in dir_name_list:  # 文件夹名前 17 个中文或 34 个英文重复
                counter += 1
                name = "{name}({counter})".format(name=name, counter=counter)
            else:
                counter = 1
            dir_name_list.append(name)
            all_dir_list.append(rec_folder(name, int(fid), size, time, None))
        return all_dir_list

    def get_rec_file_list(self, folder_id=-1) -> list:
        """获取回收站文件列表"""
        if folder_id == -1:  # 列出回收站根目录文件
            # 回收站文件夹中的文件也会显示在根目录
            html = self._get(
                self._mydisk_url, params={"item": "recycle", "action": "files"}
            )
            if not html:
                return []
            html = remove_notes(html.text)
            files = re.findall(
                r'fl_sel_ids[^\n]+value="(\d+)".+?filetype/(\w+)\.gif.+?/>\s?(.+?)(?:\.{3})?</a>.+?<td.+?>([\d\-]+?)</td>',
                html,
                re.DOTALL,
            )
            file_list = []
            file_name_list = []
            counter = 1
            for fid, ftype, name, time in sorted(files, key=lambda x: x[2]):
                if not name.endswith(ftype):  # 防止文件名太长导致丢失了文件后缀
                    name = name + "." + ftype

                if name in file_name_list:  # 防止长文件名前 17:34 个字符相同重名
                    counter += 1
                    name = "{name}({counter})".format(name=name, counter=counter)
                else:
                    counter = 1
                    file_name_list.append(name)
                file_list.append(rec_file(name, int(fid), ftype, size="", time=time))
            return file_list
        else:  # 列出回收站中文件夹内的文件,信息只有部分文件名和文件大小
            para = {
                "item": "recycle",
                "action": "folder_restore",
                "folder_id": folder_id,
            }
            html = self._get(self._mydisk_url, params=para)
            if not html or "此文件夹没有包含文件" in html.text:
                return []
            html = remove_notes(html.text)
            files = re.findall(
                r'com/(\d+?)".+?filetype/(\w+)\.gif.+?/>&nbsp;(.+?)(?:\.{3})?</a> <font color="#CCCCCC">\((.+?)\)</font>',
                html,
            )
            file_list = []
            file_name_list = []
            counter = 1
            for fid, ftype, name, size in sorted(files, key=lambda x: x[2]):
                if not name.endswith(ftype):  # 防止文件名太长丢失后缀
                    name = name + "." + ftype
                if name in file_name_list:
                    counter += 1
                    name = "{name}({counter})".format(
                        name=name, counter=counter
                    )  # 防止文件名太长且前17个字符重复
                else:
                    counter = 1
                    file_name_list.append(name)
                file_list.append(rec_file(name, int(fid), ftype, size=size, time=""))
            return file_list

    def get_rec_all(self):
        """获取整理后回收站的所有信息"""
        root_files = self.get_rec_file_list()  # 回收站根目录文件列表
        folder_list = []  # 保存整理后的文件夹列表
        for folder in self.get_rec_dir_list():  # 遍历所有子文件夹
            this_folder = rec_folder(
                folder["name"], folder["id"], folder["size"], folder["time"], []
            )
            for file in self.get_rec_file_list(
                folder["id"]
            ):  # 文件夹内的文件属性: name,id,type,size
                if find_by_id(root_files, file["id"]):  # 根目录存在同名文件
                    file["time"] = pop_by_id(root_files, file["id"])[
                        "time"
                    ]  # 从根目录删除, time 信息用来补充文件夹中的文件
                    this_folder["files"].append(file)
                else:  # 根目录没有同名文件(用户手动删了),文件还在文件夹中，只是根目录不显示，time 信息无法补全了
                    file["time"] = folder["time"]  # 那就设置时间为文件夹的创建时间
                    this_folder["files"].append(file)
            folder_list.append(this_folder)
        return root_files, folder_list

    def _get_and_post(self, para, post_data):
        html = self._get(self._mydisk_url, params=para)
        if not html:
            return CodeDetail.NETWORK_ERROR
        # 此处的 formhash 与 login 时不同，不要尝试精简这一步
        post_data["formhash"] = re.findall(
            r'name="formhash" value="(\w+?)"', html.text
        )[0]  # 设置表单 hash
        html = self._post(self._mydisk_url + "?item=recycle", post_data)
        return html

    def delete_rec(self, fid, is_file=True) -> int:
        """彻底删除回收站文件(夹)"""
        # 彻底删除后需要 1.5s 才能调用 get_rec_file() ,否则信息没有刷新，被删掉的文件似乎仍然 "存在"
        if is_file:
            para = {"item": "recycle", "action": "file_delete_complete", "file_id": fid}
            post_data = {
                "action": "file_delete_complete",
                "task": "file_delete_complete",
                "file_id": fid,
            }
        else:
            para = {
                "item": "recycle",
                "action": "folder_delete_complete",
                "folder_id": fid,
            }
            post_data = {
                "action": "folder_delete_complete",
                "task": "folder_delete_complete",
                "folder_id": fid,
            }

        # html = self._get(self._mydisk_url, params=para)
        # if not html:
        #     return CodeDetail.NETWORK_ERROR
        # # 此处的 formhash 与 login 时不同，不要尝试精简这一步
        # post_data['formhash'] = re.findall(r'name="formhash" value="(\w+?)"', html.text)[0]  # 设置表单 hash
        # html = self._post(self._mydisk_url + '?item=recycle', post_data)
        html = self._get_and_post(para, post_data)
        if not html:
            return CodeDetail.NETWORK_ERROR
        return CodeDetail.SUCCESS if "删除成功" in html.text else CodeDetail.FAILED

    def delete_rec_multi(self, *, files=None, folders=None) -> int:
        """彻底删除回收站多个文件(夹)
        :param files 文件 id 列表 List[int]
        :param folders 文件夹 id 列表 List[int]
        """
        if not files and not folders:
            return CodeDetail.FAILED
        para = {"item": "recycle", "action": "files"}
        post_data = {"action": "files", "task": "delete_complete_recycle"}
        if folders:
            post_data["fd_sel_ids[]"] = folders
        if files:
            post_data["fl_sel_ids[]"] = files
        html = self._get(self._mydisk_url, params=para)
        if not html:
            return CodeDetail.NETWORK_ERROR
        post_data["formhash"] = re.findall(
            r'name="formhash" value="(\w+?)"', html.text
        )[0]  # 设置表单 hash
        html = self._post(self._mydisk_url + "?item=recycle", post_data)
        if not html:
            return CodeDetail.NETWORK_ERROR
        return CodeDetail.SUCCESS if "删除成功" in html.text else CodeDetail.FAILED

    def recovery(self, fid, is_file=True) -> int:
        """从回收站恢复文件"""
        if is_file:
            para = {"item": "recycle", "action": "file_restore", "file_id": fid}
            post_data = {
                "action": "file_restore",
                "task": "file_restore",
                "file_id": fid,
            }
        else:
            para = {"item": "recycle", "action": "folder_restore", "folder_id": fid}
            post_data = {
                "action": "folder_restore",
                "task": "folder_restore",
                "folder_id": fid,
            }
        # html = self._get(self._mydisk_url, params=para)
        # if not html:
        #     return CodeDetail.NETWORK_ERROR
        # post_data['formhash'] = re.findall(r'name="formhash" value="(\w+?)"', html.text)[0]  # 设置表单 hash
        # html = self._post(self._mydisk_url + '?item=recycle', post_data)
        html = self._get_and_post(para, post_data)
        if not html:
            return CodeDetail.NETWORK_ERROR
        return CodeDetail.SUCCESS if "恢复成功" in html.text else CodeDetail.FAILED

    def recovery_multi(self, *, files=None, folders=None) -> int:
        """从回收站恢复多个文件(夹)"""
        if not files and not folders:
            return CodeDetail.FAILED
        para = {"item": "recycle", "action": "files"}
        post_data = {"action": "files", "task": "restore_recycle"}
        if folders:
            post_data["fd_sel_ids[]"] = folders
        if files:
            post_data["fl_sel_ids[]"] = files
        html = self._get(self._mydisk_url, params=para)
        if not html:
            return CodeDetail.NETWORK_ERROR
        post_data["formhash"] = re.findall(r'name="formhash" value="(.+?)"', html.text)[
            0
        ]  # 设置表单 hash
        html = self._post(self._mydisk_url + "?item=recycle", post_data)
        if not html:
            return CodeDetail.NETWORK_ERROR
        return CodeDetail.SUCCESS if "恢复成功" in html.text else CodeDetail.FAILED

    def recovery_all(self) -> int:
        """从回收站恢复所有文件(夹)"""
        para = {"item": "recycle", "action": "restore_all"}
        post_data = {"action": "restore_all", "task": "restore_all"}
        # first_page = self._get(self._mydisk_url, params=para)
        # if not first_page:
        #     return CodeDetail.NETWORK_ERROR
        # post_data['formhash'] = re.findall(r'name="formhash" value="(.+?)"', first_page.text)[0]  # 设置表单 hash
        # second_page = self._post(self._mydisk_url + '?item=recycle', post_data)
        second_page = self._get_and_post(para, post_data)
        if not second_page:
            return CodeDetail.NETWORK_ERROR
        return (
            CodeDetail.SUCCESS if "还原成功" in second_page.text else CodeDetail.FAILED
        )

    def get_file_list(self, folder_id=-1) -> List[dict]:
        """获取文件列表"""
        page = 1
        file_list = []
        while True:
            post_data = {"task": 5, "folder_id": folder_id, "pg": page}
            resp = self._post(self._doupload_url, post_data)
            if not resp:  # 网络异常，重试
                continue
            else:
                resp = resp.json()
            if resp["info"] == 0:
                break  # 已经拿到了全部的文件信息
            else:
                page += 1  # 下一页
            # 文件信息处理
            for file in resp["text"]:
                file_list.append(
                    File(
                        id=int(file["id"]),
                        name=file["name_all"],
                        time=time_format(file["time"]),  # 上传时间
                        size=file["size"],  # 文件大小
                        type=file["name_all"].split(".")[-1],  # 文件类型
                        downs=int(file["downs"]),  # 下载次数
                        has_pwd=True
                        if int(file["onof"]) == 1
                        else False,  # 是否存在提取码
                        has_des=True
                        if int(file["is_des"]) == 1
                        else False,  # 是否存在描述
                    )
                )
        return file_list

    def get_dir_list(self, folder_id=-1) -> []:
        """获取子文件夹列表"""
        folder_list = []
        post_data = {"task": 47, "folder_id": folder_id}
        resp = self._post(self._doupload_url, post_data)
        if not resp:
            return folder_list
        for folder in resp.json()["text"]:
            folder_list.append(
                Folder(
                    id=int(folder["fol_id"]),
                    name=folder["name"],
                    has_pwd=True if folder["onof"] == 1 else False,
                    desc=folder["folder_des"].strip("[]"),
                )
            )
        return folder_list

    def clean_ghost_folders(self):
        """清除网盘中的幽灵文件夹"""

        # 可能有一些文件夹，网盘和回收站都看不见它，但是它确实存在，移动文件夹时才会显示
        # 如果不清理掉，不小心将文件移动进去就完蛋了
        def _clean(fid):
            for folder_ in self.get_dir_list(fid):
                real_folders.append(folder_)
                _clean(folder_["id"])

        folder_with_ghost = self.get_move_folders()
        pop_by_id(folder_with_ghost, -1)  # 忽视根目录
        real_folders = []
        _clean(-1)
        for folder in folder_with_ghost:
            if not find_by_id(real_folders, folder["id"]):
                logger.debug(
                    "Delete ghost folder: {name} #{id}".format(
                        name=folder["name"], id=folder["id"]
                    )
                )
                if self.delete(folder["id"], False) != CodeDetail.SUCCESS:
                    return CodeDetail.FAILED
                if self.delete_rec(folder["id"], False) != CodeDetail.SUCCESS:
                    return CodeDetail.FAILED
        return CodeDetail.SUCCESS

    def get_full_path(self, folder_id=-1) -> []:
        """获取文件夹完整路径"""
        path_list = [FolderId("LanZouCloud", -1)]
        post_data = {"task": 47, "folder_id": folder_id}
        resp = self._post(self._doupload_url, post_data)
        if not resp:
            return path_list
        for folder in resp.json()["info"]:
            if (
                folder["folderid"] and folder["name"]
            ):  # 有时会返回无效数据, 这两个字段中某个为 None
                path_list.append(
                    FolderId(id=int(folder["folderid"]), name=folder["name"])
                )
        return path_list

    def _captcha_recognize(self, file_token):
        """识别下载时弹出的验证码,返回下载直链
        :param file_token 文件的标识码,每次刷新会变化
        """
        if not self._captcha_handler:  # 必需提前设置验证码处理函数
            logger.debug("Not set captcha handler function!")
            return None

        get_img_api = "https://vip.d0.baidupan.com/file/imagecode.php?r=" + str(
            random()
        )
        img_data = self._get(get_img_api).content
        captcha = self._captcha_handler(img_data)  # 用户手动识别验证码
        post_code_api = "https://vip.d0.baidupan.com/file/ajax.php"
        post_data = {"file": file_token, "bm": captcha}
        resp = self._post(post_code_api, post_data)
        if not resp or resp.json()["zt"] != 1:
            logger.debug("Captcha ERROR: {captcha}".format(captcha=captcha))
            return None
        logger.debug("Captcha PASS: {captcha}".format(captcha=captcha))
        return resp.json()["url"]

    def get_file_info_by_url(self, share_url, pwd="") -> dict:
        """获取文件各种信息(包括下载直链)
        :param share_url: 文件分享链接
        :param pwd: 文件提取码(如果有的话)
        """
        if not is_file_url(share_url):  # 非文件链接返回错误
            return file_detail(CodeDetail.URL_INVALID, pwd=pwd, url=share_url)

        first_page = self._get(share_url)  # 文件分享页面(第一页)
        if not first_page:
            return file_detail(CodeDetail.NETWORK_ERROR, pwd=pwd, url=share_url)

        first_page = remove_notes(first_page.text)  # 去除网页里的注释
        if "文件取消" in first_page:
            return file_detail(CodeDetail.FILE_CANCELLED, pwd=pwd, url=share_url)

        # 这里获取下载直链 304 重定向前的链接
        if "输入密码" in first_page:  # 文件设置了提取码时
            if len(pwd) == 0:
                return file_detail(
                    CodeDetail.LACK_PASSWORD, pwd=pwd, url=share_url
                )  # 没给提取码直接退出
            # data : 'action=downprocess&sign=AGZRbwEwU2IEDQU6BDRUaFc8DzxfMlRjCjTPlVkWzFSYFY7ATpWYw_c_c&p='+pwd,
            sign = re.search(r"sign=(\w+?)&", first_page).group(1)
            post_data = {"action": "downprocess", "sign": sign, "p": pwd}
            link_info = self._post(
                self._host_url + "/ajaxm.php", post_data
            )  # 保存了重定向前的链接信息和文件名
            second_page = self._get(
                share_url
            )  # 再次请求文件分享页面，可以看见文件名，时间，大小等信息(第二页)
            if not link_info or not second_page.text:
                return file_detail(CodeDetail.NETWORK_ERROR, pwd=pwd, url=share_url)
            link_info = link_info.json()
            second_page = remove_notes(second_page.text)
            # 提取文件信息
            f_name = link_info["inf"]
            f_size = re.search(r"大小.+?(\d[\d.]+\s?[BKM]?)<", second_page)
            f_size = f_size.group(1) if f_size else "0 M"
            f_time = re.search(r'class="n_file_infos">(.+?)</span>', second_page)
            f_time = time_format(f_time.group(1)) if f_time else time_format("0 小时前")
            f_desc = re.search(r'class="n_box_des">(.*?)</div>', second_page)
            f_desc = f_desc.group(1) if f_desc else ""
        else:  # 文件没有设置提取码时,文件信息都暴露在分享页面上
            para = re.search(r'<iframe.*?src="(.+?)"', first_page).group(
                1
            )  # 提取下载页面 URL 的参数
            # 文件名位置变化很多
            f_name = (
                re.search(r"<title>(.+?) - 蓝奏云</title>", first_page)
                or re.search(r'<div class="filethetext".+?>([^<>]+?)</div>', first_page)
                or re.search(r'<div style="font-size.+?>([^<>].+?)</div>', first_page)
                or re.search(r"var filename = '(.+?)';", first_page)
                or re.search(r'id="filenajax">(.+?)</div>', first_page)
                or re.search(r'<div class="b"><span>([^<>]+?)</span></div>', first_page)
            )
            f_name = f_name.group(1) if f_name else "未匹配到文件名"
            # 匹配文件时间，文件没有时间信息就视为今天，统一表示为 2020-01-01 格式
            f_time = re.search(
                r">(\d+\s?[秒天分小][钟时]?前|[昨前]天\s?[\d:]+?|\d+\s?天前|\d{4}-\d\d-\d\d)<",
                first_page,
            )
            f_time = time_format(f_time.group(1)) if f_time else time_format("0 小时前")
            # 匹配文件大小
            f_size = re.search(r"大小.+?(\d[\d.]+\s?[BKM]?)<", first_page)
            f_size = f_size.group(1) if f_size else "0 M"
            f_desc = re.search(r"文件描述.+?<br>\n?\s*(.*?)\s*</td>", first_page)
            f_desc = f_desc.group(1) if f_desc else ""
            first_page = self._get(self._host_url + para)
            if not first_page:
                return file_detail(
                    CodeDetail.NETWORK_ERROR,
                    name=f_name,
                    time=f_time,
                    size=f_size,
                    desc=f_desc,
                    pwd=pwd,
                    url=share_url,
                )
            first_page = remove_notes(first_page.text)
            # 一般情况 sign 的值就在 data 里，有时放在变量后面
            sign = re.search(r"'sign':(.+?),", first_page).group(1)
            if len(sign) < 20:  # 此时 sign 保存在变量里面, 变量名是 sign 匹配的字符
                sign = re.search(
                    r"var {sign}\s*=\s*'(.+?)';".format(sign=sign), first_page
                ).group(1)
            post_data = {"action": "downprocess", "sign": sign, "ves": 1}
            link_info = self._post(self._host_url + "/ajaxm.php", post_data)
            if not link_info:
                return file_detail(
                    CodeDetail.NETWORK_ERROR,
                    name=f_name,
                    time=f_time,
                    size=f_size,
                    desc=f_desc,
                    pwd=pwd,
                    url=share_url,
                )
            else:
                link_info = link_info.json()
        # 这里开始获取文件直链
        if link_info["zt"] == 1:
            fake_url = (
                link_info["dom"] + "/file/" + link_info["url"]
            )  # 假直连，存在流量异常检测
            download_page = self._get(fake_url, allow_redirects=False)
            if not download_page:
                return file_detail(
                    CodeDetail.NETWORK_ERROR,
                    name=f_name,
                    time=f_time,
                    size=f_size,
                    desc=f_desc,
                    pwd=pwd,
                    url=share_url,
                )
            download_page.encoding = "utf-8"
            if "网络不正常" in download_page.text:  # 流量异常，要求输入验证码
                file_token = re.findall(r"'file':'(.+?)'", download_page.text)[0]
                direct_url = self._captcha_recognize(file_token)
                if not direct_url:
                    return file_detail(
                        CodeDetail.CAPTCHA_ERROR,
                        name=f_name,
                        time=f_time,
                        size=f_size,
                        desc=f_desc,
                        pwd=pwd,
                        url=share_url,
                    )
            else:
                direct_url = download_page.headers["Location"]  # 重定向后的真直链

            f_type = f_name.split(".")[-1]
            return file_detail(
                CodeDetail.SUCCESS,
                name=f_name,
                size=f_size,
                type=f_type,
                time=f_time,
                desc=f_desc,
                pwd=pwd,
                url=share_url,
                durl=direct_url,
            )
        else:
            return file_detail(
                CodeDetail.FAILED,
                name=f_name,
                time=f_time,
                size=f_size,
                desc=f_desc,
                pwd=pwd,
                url=share_url,
            )

    def get_file_info_by_id(self, file_id) -> dict:
        """通过 id 获取文件信息"""
        info = self.get_share_info(file_id)
        if info["code"] != CodeDetail.SUCCESS:
            return file_detail(info["code"])
        return self.get_file_info_by_url(info["url"], info["pwd"])

    def get_durl_by_url(self, share_url, pwd="") -> dict:
        """通过分享链接获取下载直链"""
        file_info = self.get_file_info_by_url(share_url, pwd)
        if file_info["code"] != CodeDetail.SUCCESS:
            return direct_url_info(file_info["code"], "", "")
        return direct_url_info(CodeDetail.SUCCESS, file_info["name"], file_info["durl"])

    def get_durl_by_id(self, file_id) -> dict:
        """登录用户通过id获取直链"""
        info = self.get_share_info(file_id, is_file=True)  # 能获取直链，一定是文件
        return self.get_durl_by_url(info["url"], info["pwd"])

    def get_share_info(self, fid, is_file=True) -> dict:
        """获取文件(夹)提取码、分享链接"""
        post_data = (
            {"task": 22, "file_id": fid} if is_file else {"task": 18, "folder_id": fid}
        )  # 获取分享链接和密码用
        f_info = self._post(self._doupload_url, post_data)
        if not f_info:
            return ShareInfo(CodeDetail.NETWORK_ERROR)
        else:
            f_info = f_info.json()["info"]

        # id 有效性校验
        if ("f_id" in f_info.keys() and f_info["f_id"] == "i") or (
            "name" in f_info.keys() and not f_info["name"]
        ):
            return ShareInfo(CodeDetail.ID_ERROR)

        # onof=1 时，存在有效的提取码; onof=0 时不存在提取码，但是 pwd 字段还是有一个无效的随机密码
        pwd = f_info["pwd"] if f_info["onof"] == "1" else ""
        if "f_id" in f_info.keys():  # 说明返回的是文件的信息
            url = f_info["is_newd"] + "/" + f_info["f_id"]  # 文件的分享链接需要拼凑
            file_info = self._post(
                self._doupload_url, {"task": 12, "file_id": fid}
            )  # 文件信息
            if not file_info:
                return ShareInfo(CodeDetail.NETWORK_ERROR)
            name = file_info.json()[
                "text"
            ]  # 无后缀的文件名(获得后缀又要发送请求,没有就没有吧,尽可能减少请求数量)
            desc = file_info.json()["info"]
        else:
            url = f_info["new_url"]  # 文件夹的分享链接可以直接拿到
            name = f_info["name"]  # 文件夹名
            desc = f_info["des"]  # 文件夹描述
        return ShareInfo(CodeDetail.SUCCESS, name=name, url=url, desc=desc, pwd=pwd)

    def set_passwd(self, fid, passwd="", is_file=True) -> int:
        """设置网盘文件(夹)的提取码"""
        # id 无效或者 id 类型不对应仍然返回成功 :(
        # 文件夹提取码长度 0-12 位  文件提取码 2-6 位
        passwd_status = 0 if passwd == "" else 1  # 是否开启密码
        if is_file:
            post_data = {
                "task": 23,
                "file_id": fid,
                "shows": passwd_status,
                "shownames": passwd,
            }
        else:
            post_data = {
                "task": 16,
                "folder_id": fid,
                "shows": passwd_status,
                "shownames": passwd,
            }
        result = self._post(self._doupload_url, post_data)
        if not result:
            return CodeDetail.NETWORK_ERROR
        return CodeDetail.SUCCESS if result.json()["zt"] == 1 else CodeDetail.FAILED

    def mkdir(self, parent_id, folder_name, desc="") -> int:
        """创建文件夹(同时设置描述)"""
        folder_name = folder_name.replace(" ", "_")  # 文件夹名称不能包含空格
        folder_name = name_format(folder_name)  # 去除非法字符
        folder_list = self.get_dir_list(parent_id)
        if find_by_name(folder_list, folder_name):  # 如果文件夹已经存在，直接返回 id
            return find_by_name(folder_list, folder_name)["id"]
        raw_folders = self.get_move_folders()
        post_data = {
            "task": 2,
            "parent_id": parent_id or -1,
            "folder_name": folder_name,
            "folder_description": desc,
        }
        result = self._post(self._doupload_url, post_data)  # 创建文件夹
        if not result or result.json()["zt"] != 1:
            logger.debug(
                "Mkdir {folder_name} error, {parent_id}".format(
                    folder_name=folder_name, parent_id=parent_id
                )
            )
            return CodeDetail.MKDIR_ERROR  # 正常时返回 id 也是 int，为了方便判断是否成功，网络异常或者创建失败都返回相同错误码
        # 允许再不同路径创建同名文件夹, 移动时可通过 get_move_paths() 区分
        for folder in self.get_move_folders():
            if not find_by_id(raw_folders, folder["id"]):
                logger.debug(
                    "Mkdir {folder_name} #{id} in {parent_id}".format(
                        folder_name=folder_name, parent_id=parent_id, id=folder["id"]
                    )
                )
                return folder["id"]
        logger.debug(
            "Mkdir {folder_name} error, {parent_id}".format(
                folder_name=folder_name, parent_id=parent_id
            )
        )
        return CodeDetail.MKDIR_ERROR

    def _set_dir_info(self, folder_id, folder_name, desc="") -> int:
        """重命名文件夹及其描述"""
        # 不能用于重命名文件，id 无效仍然返回成功
        folder_name = name_format(folder_name)
        post_data = {
            "task": 4,
            "folder_id": folder_id,
            "folder_name": folder_name,
            "folder_description": desc,
        }
        result = self._post(self._doupload_url, post_data)
        if not result:
            return CodeDetail.NETWORK_ERROR
        return CodeDetail.SUCCESS if result.json()["zt"] == 1 else CodeDetail.FAILED

    def rename_dir(self, folder_id, folder_name) -> int:
        """重命名文件夹"""
        # 重命名文件要开会员额
        info = self.get_share_info(folder_id, is_file=False)
        if info["code"] != CodeDetail.SUCCESS:
            return info["code"]
        return self._set_dir_info(folder_id, folder_name, info["desc"])

    def set_desc(self, fid, desc, is_file=True) -> int:
        """设置文件(夹)描述"""
        if is_file:
            # 文件描述一旦设置了值，就不能再设置为空
            post_data = {"task": 11, "file_id": fid, "desc": desc}
            result = self._post(self._doupload_url, post_data)
            if not result:
                return CodeDetail.NETWORK_ERROR
            elif result.json()["zt"] != 1:
                return CodeDetail.FAILED
            return CodeDetail.SUCCESS
        else:
            # 文件夹描述可以置空
            info = self.get_share_info(fid, is_file=False)
            if info["code"] != CodeDetail.SUCCESS:
                return info["code"]
            return self._set_dir_info(fid, info["name"], desc)

    def rename_file(self, file_id, filename):
        """允许会员重命名文件(无法修后缀名)"""
        post_data = {
            "task": 46,
            "file_id": file_id,
            "file_name": name_format(filename),
            "type": 2,
        }
        result = self._post(self._doupload_url, post_data)
        if not result:
            return CodeDetail.NETWORK_ERROR
        return CodeDetail.SUCCESS if result.json()["zt"] == 1 else CodeDetail.FAILED

    def get_move_folders(self) -> []:
        """获取全部文件夹 id-name 列表，用于移动文件至新的文件夹"""
        # 这里 file_id 可以为任意值,不会对结果产生影响
        result = [FolderId(name="LanZouCloud", id=-1)]
        resp = self._post(self._doupload_url, data={"task": 19, "file_id": -1})
        if not resp or resp.json()["zt"] != 1:  # 获取失败或者网络异常
            return result
        info = resp.json()["info"] or []  # 新注册用户无数据, info=None
        for folder in info:
            folder_id, folder_name = int(folder["folder_id"]), folder["folder_name"]
            result.append(FolderId(folder_name, folder_id))
        return result

    def get_move_paths(self) -> List[list]:
        """获取所有文件夹的绝对路径(耗时长)"""
        # 官方 bug, 可能会返回一些已经被删除的"幽灵文件夹"
        result = []
        root = [FolderId("LanZouCloud", -1)]
        result.append(root)
        resp = self._post(self._doupload_url, data={"task": 19, "file_id": -1})
        if not resp or resp.json()["zt"] != 1:  # 获取失败或者网络异常
            return result

        ex = ThreadPoolExecutor()  # 线程数 min(32, os.cpu_count() + 4)
        id_list = [int(folder["folder_id"]) for folder in resp.json()["info"]]
        task_list = [ex.submit(self.get_full_path, fid) for fid in id_list]
        for task in as_completed(task_list):
            result.append(task.result())
        return sorted(result)

    def move_file(self, file_id, folder_id=-1) -> int:
        """移动文件到指定文件夹"""
        # 移动回收站文件也返回成功(实际上行不通) (+_+)?
        post_data = {"task": 20, "file_id": file_id, "folder_id": folder_id}
        result = self._post(self._doupload_url, post_data)
        logger.debug(
            "Move file {file_id} to {folder_id}".format(
                folder_id=folder_id, file_id=file_id
            )
        )
        if not result:
            return CodeDetail.NETWORK_ERROR
        return CodeDetail.SUCCESS if result.json()["zt"] == 1 else CodeDetail.FAILED

    def move_folder(self, folder_id, parent_folder_id=-1) -> int:
        """移动文件夹(官方并没有直接支持此功能)"""
        if folder_id == parent_folder_id or parent_folder_id < -1:
            return CodeDetail.FAILED  # 禁止移动文件夹到自身，禁止移动到 -2 这样的文件夹(文件还在,但是从此不可见)

        folder = find_by_id(self.get_move_folders(), folder_id)
        if not folder:
            logger.debug("Not found folder :{folder_id}".format(folder_id=folder_id))
            return CodeDetail.FAILED

        if self.get_dir_list(folder_id):
            logger.debug("Found subdirectory in {folder}".format(folder=folder))
            return CodeDetail.FAILED  # 递归操作可能会产生大量请求,这里只移动单层文件夹

        info = self.get_share_info(folder_id, False)
        new_folder_id = self.mkdir(
            parent_folder_id, folder["name"], info["desc"]
        )  # 在目标文件夹下创建同名文件夹

        if new_folder_id == CodeDetail.MKDIR_ERROR:
            return CodeDetail.FAILED
        elif new_folder_id == folder_id:  # 移动文件夹到同一目录
            return CodeDetail.FAILED

        self.set_passwd(new_folder_id, info["pwd"], False)  # 保持密码相同
        ex = ThreadPoolExecutor()
        task_list = [
            ex.submit(self.move_file, file["id"], new_folder_id)
            for file in self.get_file_list(folder_id)
        ]
        for task in as_completed(task_list):
            if task.result() != CodeDetail.SUCCESS:
                return CodeDetail.FAILED
        self.delete(folder_id, False)  # 全部移动完成后删除原文件夹
        self.delete_rec(folder_id, False)
        return CodeDetail.SUCCESS

    def _upload_small_file(self, file_path, folder_id=-1, file_name=None) -> int:
        """绕过格式限制上传不超过 max_size 的文件"""
        if not os.path.isfile(file_path):
            return CodeDetail.PATH_ERROR

        need_delete = False  # 上传完成是否删除
        if not is_name_valid(os.path.basename(file_path)):  # 不允许上传的格式
            if self._limit_mode:  # 不允许绕过官方限制
                return CodeDetail.OFFICIAL_LIMITED
            file_path = let_me_upload(file_path)  # 添加了报尾的新文件
            need_delete = True

        # 文件已经存在同名文件就删除
        filename = file_name or name_format(os.path.basename(file_path))
        file_list = self.get_file_list(folder_id)
        if find_by_name(file_list, filename):
            self.delete(find_by_name(file_list, filename)["id"])
        logger.debug(f"Upload {file_path} to {folder_id}")

        file = open(file_path, "rb")
        post_data = {
            "task": "1",
            "folder_id": str(folder_id),
            "id": "WU_FILE_0",
            "name": filename,
            "upload_file": (filename, file, "application/octet-stream"),
        }

        post_data = MultipartEncoder(post_data)
        tmp_header = self._headers.copy()
        tmp_header["Content-Type"] = post_data.content_type

        # MultipartEncoderMonitor 每上传 8129 bytes数据调用一次回调函数，问题根源是 httplib 库
        # issue : https://github.com/requests/toolbelt/issues/75
        # 上传完成后，回调函数会被错误的多调用一次(强迫症受不了)。因此，下面重新封装了回调函数，修改了接受的参数，并阻断了多余的一次调用
        self._upload_finished_flag = False  # 上传完成的标志

        progress = tqdm(
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=filename,
            total=post_data.len,
        )

        def _call_back(read_monitor):
            if read_monitor.len == read_monitor.bytes_read:
                self._upload_finished_flag = True
                progress.close()
            if not self._upload_finished_flag:
                progress.update(8192)

        monitor = MultipartEncoderMonitor(post_data, _call_back)

        result = self._post(up_url, data=monitor, headers=tmp_header, timeout=3600)
        if not result:  # 网络异常
            return CodeDetail.NETWORK_ERROR
        else:
            result = result.json()
        if result["zt"] != 1:
            logger.warning("Upload failed: {result}".format(result=result))
            return CodeDetail.FAILED  # 上传失败

        if need_delete:
            file.close()
            os.remove(file_path)
        return CodeDetail.SUCCESS

    def _upload_big_file(self, file_path, dir_id, file_name=None):
        """上传大文件, 且使得回调函数只显示一个文件"""
        if self._limit_mode:  # 不允许绕过官方限制
            return CodeDetail.OFFICIAL_LIMITED

        file_size = os.path.getsize(file_path)  # 原始文件的字节大小
        file_name = file_name or os.path.basename(file_path)
        tmp_dir = (
            os.path.dirname(file_path)
            + os.sep
            + "__"
            + ".".join(file_name.split(".")[:-1])
        )  # 临时文件保存路径
        record_file = (
            tmp_dir + os.sep + file_name + ".record"
        )  # 记录文件，大文件没有完全上传前保留，用于支持续传
        uploaded_size = 0  # 记录已上传字节数，用于回调函数

        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        if not os.path.exists(record_file):  # 初始化记录文件
            info = {"name": file_name, "size": file_size, "uploaded": 0, "parts": []}
            with open(record_file, "wb") as f:
                pickle.dump(info, f)
        else:
            with open(record_file, "rb") as f:
                info = pickle.load(f)
                uploaded_size = info["uploaded"]  # 读取已经上传的大小
                logger.debug(
                    "Find upload record: {uploaded_size}/{file_size}".format(
                        uploaded_size=uploaded_size, file_size=file_size
                    )
                )

        while uploaded_size < file_size:
            data_size, data_path = big_file_split(
                file_path, self._max_size, start_byte=uploaded_size
            )
            code = self._upload_small_file(data_path, dir_id)
            if code == CodeDetail.SUCCESS:
                uploaded_size += data_size  # 更新已上传的总字节大小
                info["uploaded"] = uploaded_size
                info["parts"].append(os.path.basename(data_path))  # 记录已上传的文件名
                with open(record_file, "wb") as f:
                    logger.debug(
                        "Update record file: {uploaded_size}/{file_size}".format(
                            uploaded_size=uploaded_size, file_size=file_size
                        )
                    )
                    pickle.dump(info, f)
            else:
                logger.debug(
                    "Upload data file failed: {data_path}".format(data_path=data_path)
                )
                return CodeDetail.FAILED
            os.remove(data_path)  # 删除临时数据块
            min_s, max_s = self._upload_delay  # 设置两次上传间的延时，减小封号可能性
            sleep_time = uniform(min_s, max_s)
            logger.debug(
                "Sleeping, Upload task will resume after {sleep_time}s...".format(
                    sleep_time=sleep_time
                )
            )
            sleep(sleep_time)

        # 全部数据块上传完成
        record_name = list(file_name.replace(".", ""))  # 记录文件名也打乱
        shuffle(record_name)
        record_name = name_format("".join(record_name)) + ".txt"
        record_file_new = tmp_dir + os.sep + record_name
        os.rename(record_file, record_file_new)
        code = self._upload_small_file(record_file_new, dir_id)  # 上传记录文件
        if code != CodeDetail.SUCCESS:
            logger.debug(
                "Upload record file failed: {record_file_new}".format(
                    record_file_new=record_file_new
                )
            )
            return CodeDetail.FAILED
        # 记录文件上传成功，删除临时文件
        shutil.rmtree(tmp_dir)
        logger.debug(
            "Upload finished, Delete tmp folder:{tmp_dir}".format(tmp_dir=tmp_dir)
        )
        return CodeDetail.SUCCESS

    def upload_file(self, file_path, folder_id=-1, file_name=None) -> int:
        """解除限制上传文件
        :param file_path:
        :param folder_id:
        """
        if not os.path.isfile(file_path):
            return CodeDetail.PATH_ERROR

        # 单个文件不超过 max_size 直接上传
        if os.path.getsize(file_path) <= self._max_size * 1048576:
            return self._upload_small_file(file_path, folder_id, file_name=file_name)

        # 上传超过 max_size 的文件
        if self._limit_mode:
            return CodeDetail.OFFICIAL_LIMITED

        folder_name = os.path.basename(file_path)  # 保存分段文件的文件夹名
        dir_id = self.mkdir(folder_id, folder_name, "Big File")
        if dir_id == CodeDetail.MKDIR_ERROR:
            return CodeDetail.MKDIR_ERROR  # 创建文件夹失败就退出

        return self._upload_big_file(file_path, dir_id, file_name=file_name)

    def upload_dir(self, dir_path, folder_id=-1):
        """批量上传文件夹中的文件(不会递归上传子文件夹)
        :param folder_id: 网盘文件夹 id
        :param dir_path: 文件夹路径
        """
        if not os.path.isdir(dir_path):
            return CodeDetail.PATH_ERROR

        dir_name = dir_path.split(os.sep)[-1]
        dir_id = self.mkdir(folder_id, dir_name, "批量上传")
        if dir_id == CodeDetail.MKDIR_ERROR:
            return CodeDetail.MKDIR_ERROR

        for filename in os.listdir(dir_path):
            file_path = dir_path + os.sep + filename
            if not os.path.isfile(file_path):
                continue  # 跳过子文件夹
            code = self.upload_file(file_path, dir_id)
            if code != CodeDetail.SUCCESS:
                logger.error("upload error {}".format(dir_path))
        return CodeDetail.SUCCESS

    def down_file_by_url(
        self, share_url, pwd="", save_path="./download", file_name=None
    ) -> int:
        """通过分享链接下载文件(需提取码)"""
        if not is_file_url(share_url):
            return CodeDetail.URL_INVALID
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        info = self.get_durl_by_url(share_url, pwd)
        logger.debug("File direct url info: {info}".format(info=info))
        if info["code"] != CodeDetail.SUCCESS:
            return info["code"]

        resp = self._get(info["durl"], stream=True)
        if not resp:
            return CodeDetail.FAILED
        total_size = int(resp.headers["Content-Length"])

        file_path = save_path + os.sep + info["name"]
        logger.debug("Save file to {file_path}".format(file_path=file_path))
        if os.path.exists(file_path):
            now_size = os.path.getsize(file_path)  # 本地已经下载的文件大小
        else:
            now_size = 0
        chunk_size = 4096
        last_512_bytes = b""  # 用于识别文件是否携带真实文件名信息
        header = {**self._headers, "Range": "bytes=%d-" % now_size}
        resp = self._get(info["durl"], stream=True, headers=header)

        if resp is None:  # 网络异常
            return CodeDetail.FAILED
        if resp.status_code == 416:  # 已经下载完成
            return CodeDetail.SUCCESS

        progress = tqdm(
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=info["name"],
            total=total_size,
        )

        with open(file_path, "ab") as f:
            for chunk in resp.iter_content(chunk_size):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    now_size += len(chunk)
                    if total_size - now_size < 512:
                        last_512_bytes += chunk
                    progress.update(len(chunk))
        progress.close()
        # 尝试解析文件报尾
        file_info = un_serialize(last_512_bytes[-512:])
        if (
            file_info is not None and "padding" in file_info
        ):  # 大文件的记录文件也可以反序列化出 name,但是没有 padding
            real_name = file_name or file_info["name"]
            new_file_path = save_path + os.sep + real_name
            logger.debug("Find meta info: {real_name}".format(real_name=real_name))
            if os.path.exists(new_file_path):
                os.remove(new_file_path)  # 存在同名文件则删除
            os.rename(file_path, new_file_path)
            with open(new_file_path, "rb+") as f:
                f.seek(-512, 2)  # 截断最后 512 字节数据
                f.truncate()
        return CodeDetail.SUCCESS

    def down_file_by_id(self, fid, save_path="./Download", file_name=None) -> int:
        """登录用户通过id下载文件(无需提取码)"""
        info = self.get_share_info(fid, is_file=True)
        if info["code"] != CodeDetail.SUCCESS:
            return info["code"]
        return self.down_file_by_url(
            info["url"], info["pwd"], save_path, file_name=file_name
        )

    def get_folder_info_by_url(self, share_url, dir_pwd="") -> dict:
        """获取文件夹里所有文件的信息"""
        if is_file_url(share_url):
            return FolderDetail(CodeDetail.URL_INVALID)
        try:
            html = requests.get(share_url, headers=self._headers).text
        except requests.RequestException:
            return FolderDetail(CodeDetail.NETWORK_ERROR)
        if "文件不存在" in html:
            return FolderDetail(CodeDetail.FILE_CANCELLED)
        if "请输入密码" in html and len(dir_pwd) == 0:
            return FolderDetail(CodeDetail.LACK_PASSWORD)
        try:
            # 获取文件需要的参数
            html = remove_notes(html)
            lx = re.findall(r"'lx':'?(\d)'?,", html)[0]
            t = re.findall(r"var [0-9a-z]{6} = '(\d{10})';", html)[0]
            k = re.findall(r"var [0-9a-z]{6} = '([0-9a-z]{15,})';", html)[0]
            # 文件夹的信息
            folder_id = re.findall(r"'fid':'?(\d+)'?,", html)[0]
            folder_name = re.findall(r"var.+?='(.+?)';\n.+document.title", html)[0]
            folder_time = re.findall(r'class="rets">([\d\-]+?)<a', html)[
                0
            ]  # 日期不全 %m-%d
            folder_desc = re.findall(
                r'id="filename">(.+?)</span>', html
            )  # 无描述时无法完成匹配
            folder_desc = folder_desc[0] if len(folder_desc) == 1 else ""
        except IndexError:
            return FolderDetail(CodeDetail.FAILED)

        page = 1
        files = []
        while True:
            try:
                post_data = {
                    "lx": lx,
                    "pg": page,
                    "k": k,
                    "t": t,
                    "fid": folder_id,
                    "pwd": dir_pwd,
                }
                resp = self._post(
                    self._host_url + "/filemoreajax.php",
                    data=post_data,
                    headers=self._headers,
                ).json()
            except requests.RequestException:
                return FolderDetail(CodeDetail.NETWORK_ERROR)
            if resp["zt"] == 1:  # 成功获取一页文件信息
                for f in resp["text"]:
                    files.append(
                        file_in_folder(
                            name=f["name_all"],  # 文件名
                            time=time_format(f["time"]),  # 上传时间
                            size=f["size"],  # 文件大小
                            type=f["name_all"].split(".")[-1],  # 文件格式
                            url=self._host_url + "/" + f["id"],  # 文件分享链接
                        )
                    )
                page += 1  # 下一页
                continue
            elif resp["zt"] == 2:  # 已经拿到全部的文件信息
                break
            elif resp["zt"] == 3:  # 提取码错误
                return FolderDetail(CodeDetail.PASSWORD_ERROR)
            elif resp["zt"] == 4:
                continue
            else:
                return FolderDetail(CodeDetail.FAILED)  # 其它未知错误
        # 通过文件的时间信息补全文件夹的年份(如果有文件的话)
        if files:  # 最后一个文件上传时间最早，文件夹的创建年份与其相同
            folder_time = files[-1]["time"].split("-")[0] + "-" + folder_time
        else:  # 可恶，没有文件，日期就设置为今年吧
            folder_time = datetime.today().strftime("%Y-%m-%d")
        return FolderDetail(
            CodeDetail.SUCCESS,
            file_in_folder(
                folder_name, folder_id, dir_pwd, folder_time, folder_desc, share_url
            ),
            files,
        )

    def get_folder_info_by_id(self, folder_id):
        """通过 id 获取文件夹及内部文件信息"""
        info = self.get_share_info(folder_id, is_file=False)
        if info["code"] != CodeDetail.SUCCESS:
            return FolderDetail(info["code"])
        return self.get_folder_info_by_url(info["url"], info["pwd"])

    def _check_big_file(self, file_list):
        """检查文件列表,判断是否为大文件分段数据"""
        txt_files = find_filter(
            file_list, lambda f: f["name"].endswith(".txt") and "M" not in f["size"]
        )
        if (
            txt_files and len(txt_files) == 1
        ):  # 文件夹里有且仅有一个 txt, 很有可能是保存大文件的文件夹
            try:
                info = self.get_durl_by_url(txt_files[0]["url"])
            except AttributeError:
                info = self.get_durl_by_id(txt_files[0]["id"])
            if info["code"] != CodeDetail.SUCCESS:
                logger.debug("Big file checking: Failed")
                return None
            resp = self._get(info["durl"])
            info = un_serialize(resp.content) if resp else None
            if info is not None:  # 确认是大文件
                name, size, *_, parts = (
                    info.values()
                )  # 真实文件名, 文件字节大小, (其它数据),分段数据文件名(有序)
                file_list = [find_by_name(file_list, p) for p in parts]
                if all(file_list):  # 分段数据完整
                    logger.debug(
                        "Big file checking: PASS , {name}, {size}".format(
                            name=name, size=size
                        )
                    )
                    return name, size, file_list
                logger.debug("Big file checking: Failed, Missing some data")
        logger.debug("Big file checking: Failed")
        return None

    def _down_big_file(self, name, total_size, file_list, save_path):
        """下载分段数据到一个文件，回调函数只显示一个文件
        支持大文件下载续传，下载完成后重复下载不会执行覆盖操作，直接返回状态码 SUCCESS
        """
        big_file = save_path + os.sep + name
        record_file = big_file + ".record"

        if not os.path.exists(save_path):
            os.makedirs(save_path)

        if not os.path.exists(record_file):  # 初始化记录文件
            info = {
                "last_ending": 0,
                "finished": [],
            }  # 记录上一个数据块结尾地址和已经下载的数据块
            with open(record_file, "wb") as rf:
                pickle.dump(info, rf)
        else:  # 读取记录文件，下载续传
            with open(record_file, "rb") as rf:
                info = pickle.load(rf)
                file_list = [
                    f for f in file_list if f["name"] not in info["finished"]
                ]  # 排除已下载的数据块
                logger.debug("Find download record file: {info}".format(info=info))

        progress = tqdm(
            unit="B", unit_scale=True, unit_divisor=1024, desc=name, total=total_size
        )

        with open(big_file, "ab") as bf:
            first_file = True
            for file in file_list:
                try:
                    durl_info = self.get_durl_by_url(file["url"])  # 分段文件无密码
                except AttributeError:
                    durl_info = self.get_durl_by_id(file["id"])
                if durl_info["code"] != CodeDetail.SUCCESS:
                    logger.debug("Can't get direct url: {file}".format(file=file))
                    return durl_info["code"]
                # 准备向大文件写入数据
                file_size_now = os.path.getsize(big_file)
                down_start_byte = (
                    file_size_now - info["last_ending"]
                )  # 当前数据块上次下载中断的位置
                header = {**self._headers, "Range": "bytes=%d-" % down_start_byte}
                logger.debug(
                    "Download {name}, Range: {down_start_byte}-".format(
                        name=file["name"], down_start_byte=down_start_byte
                    )
                )
                resp = self._get(durl_info["durl"], stream=True, headers=header)

                if resp is None:  # 网络错误, 没有响应数据
                    return CodeDetail.FAILED
                if (
                    resp.status_code == 416
                ):  # 下载完成后重复下载导致 Range 越界, 服务器返回 416
                    logger.debug(
                        "File {name} has already downloaded.".format(name=name)
                    )
                    os.remove(record_file)  # 删除记录文件
                    return CodeDetail.SUCCESS

                if first_file:
                    progress.update(file_size_now)
                first_file = False
                for chunk in resp.iter_content(4096):
                    if chunk:
                        file_size_now += len(chunk)
                        bf.write(chunk)
                        bf.flush()  # 确保缓冲区立即写入文件，否则下一次写入时获取的文件大小会有偏差
                        progress.update(len(chunk))

                # 一块数据写入完成，更新记录文件
                info["finished"].append(file["name"])
                info["last_ending"] = file_size_now
                with open(record_file, "wb") as rf:
                    pickle.dump(info, rf)
                logger.debug("Update download record info: {info}".format(info=info))
            # 全部数据块下载完成, 记录文件可以删除
            logger.debug(
                "Delete download record file: {record_file}".format(
                    record_file=record_file
                )
            )
            os.remove(record_file)
            progress.close()
        return CodeDetail.SUCCESS

    def down_dir_by_url(
        self, share_url, dir_pwd="", save_path="./download", *, mkdir=True
    ) -> int:
        """通过分享链接下载文件夹
        :param dir_pwd:
        :param share_url:
        :param save_path 文件夹保存路径
        :param mkdir 是否在 save_path 下创建与远程文件夹同名的文件夹
        """
        folder_detail = self.get_folder_info_by_url(share_url, dir_pwd)
        if folder_detail["code"] != CodeDetail.SUCCESS:  # 获取文件信息失败
            return folder_detail["code"]

        # 检查是否大文件分段数据
        info = self._check_big_file(folder_detail["files"])
        if info is not None:
            return self._down_big_file(*info, save_path)

        if mkdir:  # 自动创建子文件夹
            save_path = save_path + os.sep + folder_detail["folder"]["name"]
            if not os.path.exists(save_path):
                os.makedirs(save_path)

        # 不是大文件分段数据,直接下载
        for file in folder_detail["files"]:
            code = self.down_file_by_url(file["url"], dir_pwd, save_path)
            logger.debug(
                "Download file result: Code:{code}, File: {file}".format(
                    code=code, file=file
                )
            )
            if code != CodeDetail.SUCCESS:
                logger.error("download error {}".format(share_url))

        return CodeDetail.SUCCESS

    def down_dir_by_id(self, folder_id, save_path="./download", *, mkdir=True) -> int:
        """登录用户通过id下载文件夹"""
        file_list = self.get_file_list(folder_id)
        if len(file_list) == 0:
            return CodeDetail.FAILED

        # 检查是否大文件分段数据
        info = self._check_big_file(file_list)
        if info is not None:
            return self._down_big_file(*info, save_path)

        if mkdir:  # 自动创建子目录
            share_info = self.get_share_info(folder_id, False)
            if share_info["code"] != CodeDetail.SUCCESS:
                return share_info["code"]
            save_path = save_path + os.sep + share_info["name"]
            if not os.path.exists(save_path):
                logger.debug("Mkdir {save_path}".format(save_path=save_path))
                os.makedirs(save_path)

        for file in file_list:
            code = self.down_file_by_id(file["id"], save_path)
            logger.debug(
                "Download file result: Code:{code}, File: {file}".format(
                    code=code, file=file
                )
            )
            if code != CodeDetail.SUCCESS:
                logger.error("download error folder_id={}".format(folder_id))

        return CodeDetail.SUCCESS

    def down_by_url(
        self, share_url, dir_pwd="", save_path="./download", *, mkdir=True
    ) -> int:
        if is_file_url(share_url):
            return self.down_file_by_url(share_url, pwd=dir_pwd, save_path=save_path)
        elif is_folder_url(share_url):
            return self.down_dir_by_url(
                share_url, dir_pwd=dir_pwd, save_path=save_path, mkdir=mkdir
            )

    def sync_files(
        self,
        path_root,
        folder_id,
        only_directory=False,
        overwrite=False,
        filter_fun=None,
        remove_local=False,
    ):
        """
        将本地的文件同步到云端，单向同步
        :param path_root: 本地路径
        :param folder_id: 云端路径
        :param only_directory: 是否只同步文件夹
        :param overwrite: 是否需要覆盖重写
        :param filter_fun: 针对部分文件需要过滤
        :param remove_local: 同步完成后是否删除本地文件
        :return: 文件到folder_id的映射关系
        """
        yun_dir_list = self.get_dir_list(folder_id)
        yun_file_list = self.get_file_list(folder_id)
        yun_dir_dict = dict([(yun["name"], yun["id"]) for yun in yun_dir_list])
        yun_file_dict = dict([(yun["name"], yun["id"]) for yun in yun_file_list])

        file_dict = {}
        for file in os.listdir(path_root):
            local_path = os.path.join(path_root, file)
            # 根据传入的函数进行过滤，某些文件可以不同步
            if filter_fun is not None and filter_fun(local_path):
                continue

            # 文件夹同步，支持递归同步
            if os.path.isdir(local_path):
                if file in yun_dir_dict.keys():
                    yun_id = yun_dir_dict[file]
                else:
                    yun_id = self.mkdir(
                        parent_id=folder_id, folder_name=file, desc=file
                    )
                file_dict[local_path] = yun_id
                file_dict.update(self.sync_directory(local_path, yun_id))
            else:
                # 只同步文件夹
                if only_directory:
                    continue

                # 文件在云端已存在，如果覆盖重写，删除云端文件，重新上传
                if file in yun_file_dict.keys():
                    if overwrite:
                        self.delete(yun_file_dict[file], is_file=True)
                        yun_id = self.upload_file(
                            file_path=local_path, folder_id=folder_id
                        )
                    else:
                        yun_id = yun_file_dict[file]
                else:
                    yun_id = self.upload_file(file_path=local_path, folder_id=folder_id)
                file_dict[local_path] = yun_id
                if remove_local:
                    os.remove(local_path)

        return file_dict

    def sync_directory(self, path_root, folder_id):
        return self.sync_files(path_root, folder_id, only_directory=True)


def download(url, dir_pwd="./download"):
    downer = LanZouCloud()
    downer.ignore_limits()
    downer.down_by_url(url, save_path=dir_pwd)
