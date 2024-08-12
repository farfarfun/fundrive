import json
import os.path

from fundrive.core import BaseDrive


class DriveTable:
    def __init__(self, db_name, table_name, drive: BaseDrive, drive_root=""):
        self.db_name = db_name
        self.table_name = table_name
        self.drive_root = drive_root
        self.drive = drive

    @property
    def table_path(self):
        return os.path.join(self.drive_root, self.db_name, self.table_name)

    @property
    def meta_path(self):
        return os.path.join(self.table_path, "_meta")

    def partition_path(self, partition="all"):
        return os.path.join(self.table_path, partition)

    def file_path(self, partition, filename="all"):
        return os.path.join(self.partition_path(partition), filename)

    def partition_meta_path(self):
        return os.path.join(self.meta_path, "partition.json")

    def update_partition_meta(self, refresh=False, *args, **kwargs):
        tmp = "./partition.json"
        self.drive.download_file(local_path=tmp, drive_path=self.partition_meta_path())
        partition_meta = []
        if os.path.exists(tmp):
            with open(tmp, "r") as f:
                partition_meta = json.load(f)
        partition_meta = dict([file["path"], file] for file in partition_meta)
        for dir_info in self.drive.get_dir_list(self.table_path):
            dir_path = dir_info["path"]
            if os.path.basename(dir_path).startswith("_"):
                continue
            print(dir_info)
            for file_info in self.drive.get_file_list(dir_path):
                partition_meta[file_info["path"]] = file_info
        with open(tmp, "w") as f:
            json.dump(list(partition_meta.values()), f)
        self.drive.upload_file(local_path=tmp, drive_path=self.partition_meta_path())
        os.remove(tmp)

    def partition_meta(self):
        tmp = "./partition.json"
        self.drive.download_file(local_path=tmp, drive_path=self.partition_meta_path())
        if not os.path.exists(tmp):
            return None
        with open(tmp, "r") as f:
            return json.load(f)

