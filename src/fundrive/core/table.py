import json
import logging
import os.path

from fundrive import LanZouDrive
from fundrive.core import BaseDrive


class DriveTable:
    def __init__(self, table_fid, drive: BaseDrive, drive_root=""):
        self.table_fid = table_fid
        self.drive_root = drive_root
        self.drive = drive
        self._fid_par_dict = {}
        self._fid_meta = None
        self._fid_meta_partition_json = None

    @property
    def __meta_partition_json(self):
        return "./partition.tar"

    def cache_partition(self):
        for file in self.drive.get_dir_list(self.table_fid):
            self._fid_par_dict[file["name"]] = file["fid"]

        if "_meta" in self._fid_par_dict.keys():
            self._fid_meta = self._fid_par_dict["_meta"]
        else:
            self._fid_meta = self.drive.mkdir(fid=self.table_fid, name="_meta")

        for file in self.drive.get_file_list(self._fid_meta):
            if file["name"] == os.path.basename(self.__meta_partition_json):
                self._fid_meta_partition_json = file["fid"]
        print(f"partition_size={len(self._fid_par_dict)}")
        print(f" _fid_meta_partition_json={self._fid_meta_partition_json}")

    @property
    def meta_path(self):
        if len(self._fid_par_dict) == 0:
            self.cache_partition()

        return self._fid_meta

    def upload(self, file, partition):
        if partition in self._fid_par_dict.keys():
            fid = self._fid_par_dict[partition]
        else:
            logging.info(f" partition={partition} not exists,create it.")
            fid = self.drive.mkdir(fid=self.table_fid, name=partition)
            self.cache_partition()
        self.drive.upload_file(fid=fid, local_path=file)

    def update_partition_meta(self, refresh=False, *args, **kwargs):
        tmp = self.__meta_partition_json
        print(f"download {self.__meta_partition_json}")
        if self._fid_meta_partition_json is not None:
            self.drive.download_file(fid=self._fid_meta_partition_json, local_dir="./")
        partition_meta = []
        if os.path.exists(tmp):
            with open(tmp, "r") as f:
                partition_meta = json.load(f)

        partition_meta = dict([file["name"], file] for file in partition_meta)
        for partition_name, partition_fid in self._fid_par_dict.items():
            if partition_name.startswith("_"):
                continue

            for file in self.drive.get_file_list(partition_fid):
                partition_meta[file["name"]] = file.fid
        print(f"file size={len(partition_meta)}")
        with open(tmp, "w") as f:
            json.dump(list(partition_meta.values()), f)
        self.drive.upload_file(local_path=tmp, fid=self._fid_meta_partition_json)
        os.remove(tmp)

    def partition_meta(self):
        tmp = self.__meta_partition_json
        if os.path.exists(tmp):
            os.remove(tmp)

        if self._fid_meta_partition_json is not None:
            self.drive.download_file(local_dir="./", fid=self._fid_meta_partition_json)
        if not os.path.exists(tmp):
            return {}
        with open(tmp, "r") as f:
            return json.load(f)
