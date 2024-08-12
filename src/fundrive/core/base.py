import os
from typing import Any, List, Dict


class BaseDrive:
    def __init__(self, *args, **kwargs):
        pass

    def login(self, *args, **kwargs) -> bool:
        """
        登录
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def mkdir(self, path, exist_ok=True, *args, **kwargs) -> bool:
        """
        创建目录
        :param exist_ok:
        :param path:
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def exist(self, path, *args, **kwargs) -> bool:
        raise NotImplementedError()

    def delete(self, path, *args, **kwargs) -> bool:
        """
        删除
        :param path:
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def get_file_list(self, path, *args, **kwargs) -> List[Dict[str, Any]]:
        """
        获取文件列表
        :param path:
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def get_dir_list(self, path, *args, **kwargs) -> List[Dict[str, Any]]:
        """
        获取目录列表
        :param path:
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def get_file_info(self, path, *args, **kwargs) -> Dict[str, Any]:
        """
        获取文件信息
        :param path:
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def get_dir_info(self, path, *args, **kwargs) -> Dict[str, Any]:
        """
        获取目录信息
        :param path:
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def download_file(
        self, local_path, drive_path, overwrite=False, *args, **kwargs
    ) -> bool:
        """
        下载文件
        :param local_path:
        :param drive_path:
        :param overwrite:
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def download_dir(
        self, local_path, drive_path, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        """
        下载目录
        :param local_path:
        :param drive_path:
         :param recursion:
        :param overwrite:
        :param args:
        :param kwargs:
        :return:
        """
        if not self.exist(drive_path):
            return False
        if not os.path.exists(local_path):
            os.makedirs(local_path, exist_ok=True)
        for file in self.get_file_list(drive_path):
            _drive_path = file["path"]
            _local_path = os.path.join(local_path, os.path.basename(_drive_path))
            self.download_file(
                local_path=_local_path,
                drive_path=_drive_path,
                overwrite=overwrite,
                *args,
                **kwargs
            )
        if not recursion:
            return True

        for file in self.get_dir_list(drive_path):
            _drive_path = file["path"]
            _local_path = os.path.join(local_path, os.path.basename(_drive_path))
            self.download_dir(
                local_path=_local_path,
                drive_path=_drive_path,
                overwrite=overwrite,
                recursion=recursion,
                *args,
                **kwargs
            )

    def upload_file(
        self, local_path, drive_path, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        """
        上传文件
        :param local_path:
        :param drive_path:
        :param recursion:
        :param overwrite:
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def upload_dir(
        self, local_path, drive_path, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        """
        上传目录
        :param local_path:
        :param drive_path:
         :param recursion:
        :param overwrite:
        :param args:
        :param kwargs:
        :return:
        """
        if not os.path.exists(local_path):
            return False
        for file in os.listdir(local_path):
            _local_path = os.path.join(local_path, file)
            _drive_path = os.path.join(drive_path, file)
            if not self.exist(_drive_path):
                self.mkdir(drive_path)
            if os.path.isfile(_local_path):
                self.upload_file(
                    local_path=_local_path,
                    drive_path=_drive_path,
                    overwrite=overwrite,
                    *args,
                    **kwargs
                )
            elif recursion:
                self.upload_dir(
                    local_path=_local_path,
                    drive_path=_drive_path,
                    recursion=recursion,
                    overwrite=overwrite,
                    *args,
                    **kwargs
                )
