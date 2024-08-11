from typing import Any, List, Dict


class DriveSystem:
    def __init__(self, *args, **kwargs):
        pass

    def login(self, *args, **kwargs) -> bool:
        raise NotImplementedError()

    def mkdir(self, path, *args, **kwargs) -> bool:
        raise NotImplementedError()

    def delete(self, *args, **kwargs) -> bool:
        raise NotImplementedError()

    def get_file_list(self, *args, **kwargs) -> List[Dict[str, Any]]:
        raise NotImplementedError()

    def get_dir_list(self, *args, **kwargs) -> List[Dict[str, Any]]:
        raise NotImplementedError()

    def get_file_info(self, *args, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError()

    def get_dir_info(self, *args, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError()

    def download_file(self, dir_path="./cache", overwrite=False, *args, **kwargs) -> bool:
        raise NotImplementedError()

    def download_dir(self, dir_path="./cache", overwrite=False, *args, **kwargs) -> bool:
        raise NotImplementedError()

    def upload_file(self, file_path="./cache", overwrite=False, *args, **kwargs) -> bool:
        raise NotImplementedError()

    def upload_dir(self, dir_path="./cache", overwrite=False, *args, **kwargs) -> bool:
        raise NotImplementedError()
