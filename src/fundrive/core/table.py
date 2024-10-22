import json
import logging
import os.path

from fundrive.core import BaseDrive

logger = logging.getLogger("fundrive")


class DriveTable:
    def __init__(self, table_fid, drive: BaseDrive):
        self.table_fid = table_fid
        self.drive = drive

        self._fid_par_dict = {}
        self._fid_meta = None
        self._fid_meta_par = None

    @property
    def __local_meta_path(self):
        cache_dir = f"{os.environ['HOME']}/.cache/fundrive/table/{self.table_fid}"
        os.makedirs(cache_dir, exist_ok=True)
        return f"{cache_dir}/partition.tar"

    @property
    def meta_path(self):
        if len(self._fid_par_dict) == 0:
            self.update_partition_dict()

        return self._fid_meta

    def update_partition_dict(self):
        for file in self.drive.get_dir_list(self.table_fid):
            self._fid_par_dict[file["name"]] = file["fid"]

        if "_meta" in self._fid_par_dict.keys():
            self._fid_meta = self._fid_par_dict["_meta"]
        else:
            self._fid_meta = self.drive.mkdir(fid=self.table_fid, name="_meta")

        for file in self.drive.get_file_list(self._fid_meta):
            if file["name"] == os.path.basename(self.__local_meta_path):
                self._fid_meta_par = file["fid"]
        logger.info(f"partition_size={len(self._fid_par_dict)}")
        logger.info(f"fid_meta_par={self._fid_meta_par}")
        logger.info(f"fid_meta={self._fid_meta}")

    def upload(self, file, partition, overwrite=False):
        if partition in self._fid_par_dict.keys():
            fid = self._fid_par_dict[partition]
        else:
            logging.info(f" partition={partition} not exists,create it.")
            fid = self.drive.mkdir(fid=self.table_fid, name=partition)
            self.update_partition_dict()
        self.drive.upload_file(fid=fid, local_path=file, overwrite=overwrite)

    def update_partition_meta(self, refresh=False, *args, **kwargs):
        if self._fid_meta is None:
            self.update_partition_dict()
        local_meta_path = self.__local_meta_path

        partition_meta = [] if refresh else self.partition_meta(refresh=True)
        logger.info(f"exists meta size={len(partition_meta)}")

        partition_meta = dict([file["name"], file] for file in partition_meta)
        for partition_name, partition_fid in self._fid_par_dict.items():
            if partition_name.startswith("_"):
                continue

            for file in self.drive.get_file_list(fid=partition_fid):
                partition_meta[file["name"]] = file

        logger.info(f"update meta size={len(partition_meta)}")
        logger.info(f"upload meta file to {self._fid_meta}")
        json.dump(list(partition_meta.values()), open(local_meta_path, "w"))
        self.drive.upload_file(local_path=local_meta_path, fid=self._fid_meta, overwrite=True)

    def partition_meta(self, refresh=False):
        tmp = self.__local_meta_path

        if not os.path.exists(tmp) or refresh:
            if os.path.exists(tmp):
                os.remove(tmp)

            if self._fid_meta_par is not None:
                self.drive.download_file(local_dir=os.path.dirname(tmp), fid=self._fid_meta_par)
        if os.path.exists(tmp):
            return json.load(open(tmp, "r"))
        else:
            return []
