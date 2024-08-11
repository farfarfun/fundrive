import os
from typing import Any, Dict, List

import requests
from fundrive.core import DriveSystem
from fundrive.download import simple_download
from funsecret import read_secret


class OpenDataLabDrive(DriveSystem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = "https://openxlab.org.cn"
        self.cookies = {}
        self.headers = {}

    def login(
        self, ak=None, sk=None, opendatalab_session=None, ssouid=None, *args, **kwargs
    ) -> bool:
        self.cookies.update(
            {
                "opendatalab_session": opendatalab_session
                or read_secret(
                    cate1="fundrive",
                    cate2="opendatalab",
                    cate3="cookies",
                    cate4="opendatalab_session",
                ),
                "ssouid": ssouid
                or read_secret(
                    cate1="fundrive",
                    cate2="opendatalab",
                    cate3="cookies",
                    cate4="ssouid",
                ),
            }
        )
        self.headers.update({"accept": "application/json"})
        return True

    def get_file_info(self, dataset_id, file_path, *args, **kwargs) -> Dict[str, Any]:
        resp = requests.get(
            url=f"{self.host}/datasets/resolve/{dataset_id}/main/{file_path}",
            headers=self.headers,
            cookies=self.cookies,
            allow_redirects=False,
            stream=True,
        )
        result = {
            "url": resp.headers["Location"],
            "dataset_id": dataset_id,
            "path": file_path[1:],
            "size": resp.headers.get("content-length", 0),
        }
        return result

    def get_file_list(
        self, dataset_name, payload=None, *args, **kwargs
    ) -> List[Dict[str, Any]]:
        dataset_name = dataset_name.replace("/", ",")
        data = {"recursive": True}
        if payload:
            data.update(payload)
        resp = requests.get(
            url=f"{self.host}/datasets/api/v2/datasets/{dataset_name}/r/main",
            params=data,
            headers=self.headers,
            cookies=self.cookies,
        )
        result_dict = resp.json()["data"]["list"]
        return result_dict

    def download_file(
        self,
        dir_path="./cache",
        dataset_id=None,
        file_path=None,
        overwrite=False,
        *args,
        **kwargs,
    ) -> bool:
        try:
            file_info = self.get_file_info(dataset_id=dataset_id, file_path=file_path)
            filepath = os.path.join(dir_path, file_info["path"])
            if (
                os.path.exists(filepath)
                and not overwrite
                and file_info["size"] == os.path.getsize(filepath)
            ):
                return False
            return simple_download(
                url=file_info["url"],
                filepath=os.path.join(dir_path, file_info["path"]),
                overwrite=overwrite,
                *args,
                **kwargs,
            )
        except Exception as e:
            return False

    def download_dir(
        self, dir_path="./cache", dataset_name=None, overwrite=False, *args, **kwargs
    ) -> bool:
        if dataset_name is None:
            return False
        file_list = self.get_file_list(dataset_name=dataset_name)
        for i, file in enumerate(file_list):
            filepath = os.path.join(dir_path, file["path"])
            if (
                os.path.exists(filepath)
                and not overwrite
                and file["size"] == os.path.getsize(filepath)
            ):
                return False
            try:
                self.download_file(
                    dir_path=dir_path,
                    dataset_id=file["dataset_id"],
                    file_path=file["path"],
                    overwrite=overwrite,
                    prefix=f"{i}/{len(file_list)}",
                )
            except Exception as e:
                print(e)
        return True
