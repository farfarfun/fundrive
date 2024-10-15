import subprocess
from typing import List

from funsecret import read_secret

from fundrive.core import BaseDrive
from fundrive.core.base import DriveFile


class AlipanDrive(BaseDrive):
    def __init__(self, *args, **kwargs):
        super(AlipanDrive, self).__init__(*args, **kwargs)
        from aligo import Aligo

        self.drive = Aligo()

    def login(self, server_url=None, username=None, password=None, *args, **kwargs) -> bool:
        refresh_token = username or read_secret("fundrive", "drives", "alipan", "refresh_token")
        try:
            from aligo import Aligo
        except Exception as e:
            subprocess.check_call(["pip", "install", "fundrive-alipan"])
            from aligo import Aligo
        self.drive = Aligo(refresh_token=refresh_token)
        return True

    def mkdir(self, fid, name, return_if_exist=True, *args, **kwargs) -> str:
        return self.drive.create_folder(parent_file_id=fid, name=name).file_id

    def delete(self, fid, *args, **kwargs) -> bool:
        self.drive.move_file_to_trash(file_id=fid)
        return True

    def exist(self, fid, *args, **kwargs) -> bool:
        return self.drive.get_file(file_id=fid) is not None

    def get_file_list(self, fid="root", *args, **kwargs) -> List[DriveFile]:
        result = []
        for file in self.drive.get_file_list(parent_file_id=fid):
            if file.type == "file":
                result.append(DriveFile(fid=file.file_id, name=file.name, size=file.size))
        return result

    def get_dir_list(self, fid="root", *args, **kwargs) -> List[DriveFile]:
        result = []
        for file in self.drive.get_file_list(parent_file_id=fid):
            if file.type == "folder":
                result.append(DriveFile(fid=file.file_id, name=file.name, size=file.size))
        return result

    def get_file_info(self, fid, *args, **kwargs) -> DriveFile:
        res = self.drive.get_file(file_id=fid)
        return DriveFile(fid=res.file_id, name=res.name, size=res.size)

    def get_dir_info(self, fid, *args, **kwargs) -> DriveFile:
        res = self.drive.get_file(file_id=fid)
        return DriveFile(fid=res.file_id, name=res.name, size=res.size)

    def download_file(self, fid, local_dir, overwrite=False, *args, **kwargs) -> bool:
        self.drive.download_file(file_id=fid, local_folder=local_dir)
        return True

    def upload_file(self, local_path, fid, recursion=True, overwrite=False, *args, **kwargs) -> bool:
        self.drive.upload_file(
            file_path=local_path, parent_file_id=fid, check_name_mode="overwrite" if overwrite else "refuse"
        )
        return True
