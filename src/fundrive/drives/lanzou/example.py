#!/usr/bin/env python3
"""
蓝奏云驱动示例

默认只做只读操作（登录 + 列目录），不会上传或删除任何内容。

使用方法：
- python -m fundrive.drives.lanzou.example               # 登录后列根目录
- python -m fundrive.drives.lanzou.example --fid 2192474 # 列指定目录
- python -m fundrive.drives.lanzou.example --url <分享链接> --pwd <提取密码>

配置方法（登录模式需要）：
    funsecret set fundrive drives funlanzou ylogin "****"
    funsecret set fundrive drives funlanzou phpdisk_info "****"
"""

import argparse

from farlog import getLogger

from fundrive.drives.lanzou import LanZouDrive

logger = getLogger("fundrive.lanzou.example")


def build_parser() -> argparse.ArgumentParser:
    """
    构造命令行参数解析器

    Returns:
        argparse.ArgumentParser: 已配置好参数的解析器
    """
    parser = argparse.ArgumentParser(description="蓝奏云驱动只读示例")
    parser.add_argument("--fid", default="-1", help="目录ID，-1 表示根目录（登录模式）")
    parser.add_argument("--url", default=None, help="文件夹分享链接（免登录模式）")
    parser.add_argument("--pwd", default=None, help="分享链接的提取密码")
    return parser


def list_by_share(url: str, pwd: str | None) -> int:
    """
    免登录：按分享链接列出文件

    Args:
        url (str): 文件夹分享链接
        pwd (str | None): 提取密码，无密码分享传 ``None``

    Returns:
        int: 进程退出码，0 表示成功
    """
    drive = LanZouDrive()
    drive.instance()
    files = drive.get_file_list(fid=None, url=url, pwd=pwd)
    logger.info("分享链接内共 {} 个文件", len(files))
    for item in files:
        logger.info("📄 {}  size={}  url={}", item["name"], item["size"], item["url"])
    return 0


def list_by_login(fid: str) -> int:
    """
    登录模式：列出指定目录下的子目录与文件

    Args:
        fid (str): 目录ID，``-1`` 表示根目录

    Returns:
        int: 进程退出码，0 表示成功，1 表示登录失败
    """
    drive = LanZouDrive()
    if not drive.login():
        logger.error("登录失败，请先用 funsecret 配置 ylogin / phpdisk_info")
        return 1

    folder_id = int(fid) if str(fid).lstrip("-").isdigit() else fid
    for item in drive.get_dir_list(fid=folder_id):
        logger.info("📁 {}  fid={}", item["name"], item["fid"])
    for item in drive.get_file_list(fid=folder_id):
        logger.info("📄 {}  fid={}", item["name"], item["fid"])
    return 0


def main() -> int:
    """
    示例入口：有 ``--url`` 走免登录分享模式，否则走登录模式

    Returns:
        int: 进程退出码
    """
    args = build_parser().parse_args()
    if args.url:
        return list_by_share(args.url, args.pwd)
    return list_by_login(args.fid)


if __name__ == "__main__":
    raise SystemExit(main())
