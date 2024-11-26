import os
import shutil
from typing import Any, List, Dict

from fundrive.core import BaseDrive


class OSDrive(BaseDrive):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def exist(self, path, *args, **kwargs) -> bool:
        return os.path.exists(path)

    def mkdir(self, path, exist_ok=True, *args, **kwargs) -> bool:
        os.makedirs(path, exist_ok=exist_ok)
        return True

    def upload_file(
        self, local_path, drive_path, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        if not os.path.exists(local_path):
            return False
        print(local_path, drive_path)
        shutil.copyfile(local_path, drive_path)
        return True

    def download_file(
        self, local_path, drive_path, overwrite=False, *args, **kwargs
    ) -> bool:
        if not os.path.exists(drive_path):
            return False
        print(local_path, drive_path)
        shutil.copyfile(drive_path, local_path)
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
