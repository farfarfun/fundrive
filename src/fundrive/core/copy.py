"""跨网盘目录搬运：先下载到本地临时目录，再整目录上传到目标网盘。"""

import shutil
import tempfile

from fundrive.core import BaseDrive


def copy_data(drive1: BaseDrive, drive2: BaseDrive, from_fid: str, to_fid: str) -> bool:
    """
    把 ``drive1`` 上的一个目录整体复制到 ``drive2`` 的指定目录下

    中转目录用 :func:`tempfile.mkdtemp` 创建并在结束后删除，不再往进程当前工作目录
    写 ``tmp/``。

    Args:
        drive1 (BaseDrive): 源网盘驱动（需已登录）
        drive2 (BaseDrive): 目标网盘驱动（需已登录）
        from_fid (str): 源目录ID
        to_fid (str): 目标父目录ID，复制结果是它下面的一个同名子目录

    Returns:
        bool: 复制是否成功

    Raises:
        ValueError: 源目录不存在，或在目标网盘创建同名目录失败
    """
    info = drive1.get_dir_info(from_fid)
    if not info:
        raise ValueError(f"源目录不存在或无法读取: fid={from_fid}")

    # mkdir 按 BaseDrive 契约返回**新目录的ID**，不是布尔值；
    # 历史实现把返回值直接赋给 to_fid，驱动若返回 bool 就会把 True 当成目录ID用。
    new_fid = drive2.mkdir(fid=to_fid, name=info["name"])
    if not new_fid or isinstance(new_fid, bool):
        raise ValueError(
            f"在目标网盘创建目录失败: parent_fid={to_fid} name={info['name']}"
        )

    local_dir = tempfile.mkdtemp(prefix="fundrive-copy-")
    try:
        if not drive1.download_dir(fid=from_fid, save_dir=local_dir):
            return False
        return bool(drive2.upload_dir(filedir=local_dir, fid=new_fid))
    finally:
        shutil.rmtree(local_dir, ignore_errors=True)
