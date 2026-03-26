import os
import shutil
from typing import Any, List, Dict, Optional

from fundrive.core import BaseDrive


class OSDrive(BaseDrive):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        return os.path.exists(fid)

    def mkdir(self, path, exist_ok=True, *args, **kwargs) -> bool:
        os.makedirs(path, exist_ok=exist_ok)
        return True

    def upload_file(
        self, filepath: str, fid: str, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        if not os.path.exists(filepath):
            return False
        print(filepath, fid)
        shutil.copyfile(filepath, fid)
        return True

    def download_file(
        self,
        fid: str,
        save_dir: Optional[str] = None,
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
        overwrite: bool = False,
        *args,
        **kwargs,
    ) -> bool:
        """
        下载单个文件

        Args:
            fid: 文件ID（源文件路径）
            save_dir: 文件保存目录
            filename: 文件名
            filepath: 完整的文件保存路径
            overwrite: 是否覆盖已存在的文件

        Returns:
            bool: 下载是否成功
        """
        # 检查源文件是否存在
        if not os.path.exists(fid):
            return False

        # 确定保存路径
        if filepath:
            local_path = filepath
        elif save_dir and filename:
            local_path = os.path.join(save_dir, filename)
        elif save_dir:
            local_path = os.path.join(save_dir, os.path.basename(fid))
        else:
            local_path = os.path.basename(fid)

        # 检查文件是否已存在
        if os.path.exists(local_path) and not overwrite:
            return False

        # 确保目录存在
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # 执行复制
        shutil.copyfile(fid, local_path)
        return True

    def get_file_list(self, path, *args, **kwargs) -> List[Dict[str, Any]]:
        result = []
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path):
                result.append({"path": file_path})
        return result

    def get_dir_list(self, path, *args, **kwargs) -> List[Dict[str, Any]]:
        result = []
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isdir(file_path):
                result.append({"path": file_path})
        return result


class LocalDrive(OSDrive):
    pass
