from datetime import datetime


class DriveSnapshot:
    def __init__(self, version_num=20, *args, **kwargs):
        self.version_num = version_num

    def _tar_path(self, file_path):
        return f"{file_path}-{datetime.now().strftime('%Y%m%d%H%M%S')}.tar"

    def update(self, file_path, *args, **kwargs):
        pass

    def download(self, dir_path, *args, **kwargs):
        pass
