import os

from funfile.compress import tarfile

from fundrive.core import DriveSnapshot

from .drive import LanZouDrive


class LanZouSnapshot(DriveSnapshot):
    def __init__(self, fid=None, url=None, pwd="", *args, **kwargs):
        super(LanZouSnapshot, self).__init__(*args, **kwargs)
        self.drive = LanZouDrive()
        self.fid = fid
        self.url = url
        self.pwd = pwd

    def delete_outed_version(self):
        datas = self.drive.get_file_list(path=self.fid)
        datas = sorted(datas, key=lambda x: x["name"], reverse=True)
        if len(datas) > self.version_num:
            for i in range(self.version_num, len(datas)):
                self.drive.delete(datas[i]["fid"], is_file=True)

    def update(self, file_path, *args, **kwargs):
        gz_path = self._tar_path(file_path)
        tarfile.file_entar(file_path, gz_path)
        self.drive.login()
        self.drive.upload_file(gz_path, drive_path=self.fid)
        os.remove(gz_path)
        self.delete_outed_version()

    def download(self, dir_path, *args, **kwargs):
        self.drive.instance()
        datas = self.drive.get_file_list(url=self.url, pwd=self.pwd)
        if len(datas) == 0:
            print("没有快照文件")
            return
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        datas = sorted(datas, key=lambda x: x["name"], reverse=True)
        self.drive.download_file(
            dir_path=dir_path,
            url=datas[0]["url"] + "," + datas[0]["pwd"],
            overwrite=True,
        )
        tar_path = f"{dir_path}/{datas[0]['name']}"
        tarfile.file_detar(tar_path)
        os.remove(tar_path)
