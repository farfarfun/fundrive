import json
import os
from typing import List

import requests
from fundrive.core import BaseDrive, DriveFile
from funget import simple_download
from funsecret import read_secret
from funutil import getLogger

logger = getLogger("fundrive")


class ZenodoDrive(BaseDrive):
    def __init__(self, sandbox=False):
        super().__init__()
        self.access_token = None
        self.base_url = (
            "https://sandbox.zenodo.org/api" if sandbox else "https://zenodo.org/api"
        )

    def check_token(self):
        if not isinstance(self.access_token, str) or not self.access_token:
            logger.error("Token need to be a string")
        r = requests.get(
            f"{self.base_url}/deposit/depositions",
            params={"access_token": self.access_token},
        )
        if r.status_code != 200:
            logger.error(
                f"Token accept error, status code: {r.status_code}  {r.json()['message']}"
            )
        logger.success("access token success")

    def login(self, access_token=None, *args, **kwargs) -> bool:
        self.access_token = access_token or read_secret(
            "fundrive", "zenodo", "access_token"
        )
        return True

    def get_file_info(
        self, fid=None, record_id=None, filepath=None, *args, **kwargs
    ) -> DriveFile:
        url = fid
        if record_id is not None and fid is not None:
            url = f"{self.base_url}/records/{record_id}/files/{filepath}"
        response = requests.get(url, *args, **kwargs).json()
        return DriveFile(fid=url, name=response["key"], **response)

    def get_file_list(self, record_id, *args, **kwargs) -> List[DriveFile]:
        url = f"{self.base_url}/records/{record_id}"
        response = requests.get(url).json()
        print(response)
        result = []
        for file in response["files"]:
            result.append(
                DriveFile(
                    fid=file["links"]["self"].rstrip("/content"),
                    path=file["key"],
                    name=file["key"],
                    size=file["size"],
                    url=file["links"]["self"],
                )
            )
        return result

    def get_dir_list(self, record_id, *args, **kwargs) -> List[DriveFile]:
        return self.get_file_list(record_id, *args, **kwargs)

    def download_file(
        self, record_id, local_dir, overwrite=False, *args, **kwargs
    ) -> bool:
        for file in self.get_file_list(record_id, *args, **kwargs):
            simple_download(url=file["url"], filepath=f"{local_dir}/{file['key']}")
        return True

    def download_dir(
        self, record_id, local_dir, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        return self.download_file(
            record_id, local_dir, overwrite=overwrite, *args, **kwargs
        )

    def mkdir(self, fid=None, name=None, return_if_exist=True, *args, **kwargs) -> dict:
        r = requests.post(
            f"{self.base_url}/deposit/depositions",
            params={"access_token": self.access_token},
            json={},
            headers={"Content-Type": "application/json"},
        )

        if r.status_code != 201:
            logger.error(
                f"Error in creation, status code: {r.status_code}   {r.json()['message']}"
            )
        # deposition_id = r.json()["id"]
        # bucket_url = r.json()["links"]["bucket"]
        return r.json()

    def upload_file(
        self,
        local_path,
        record_id=None,
        bucket_url=None,
        recursion=True,
        overwrite=False,
        *args,
        **kwargs,
    ) -> bool:
        filename = os.path.basename(local_path)
        # old API
        if record_id is not None:
            r = requests.post(
                url=f"{self.base_url}/deposit/depositions/{record_id}/files",
                params={"access_token": self.access_token},
                data={"name": filename},
                files={"file": open(local_path, "rb")},
            )
            if r.status_code != 201:
                logger.error(
                    f"Error in data upload, status code: {r.status_code}   {r.json()['message']}"
                )
                return False
            return True

        # new API
        if bucket_url is None:
            bucket_url = self.mkdir()["links"]["bucket"]

        with open(local_path, "rb") as fp:
            r = requests.put(
                url=f"{bucket_url}/{os.path.basename(local_path)}",
                params={"access_token": self.access_token},
                data=fp,
            )
        print(json.dumps(r.json(), indent=2))
        logger.success(
            f"{local_path} ID = {record_id} (DOI: 10.5281/zenodo.{record_id})"
        )
        return True

    def update_meta(
        self,
        record_id=None,
        title="My first upload",
        description="My first upload",
        names="fundrive",
        creators=None,
    ):
        data = {
            "metadata": {
                "title": title,
                "upload_type": "poster",
                "description": description,
                "creators": creators
                or [
                    {"name": name, "affiliation": "farfarfun"}
                    for name in names.split(",")
                ],
            }
        }
        r = requests.put(
            f"https://zenodo.org/api/deposit/depositions/{record_id}",
            params={"access_token": self.access_token},
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )
        if r.status_code != 200:
            logger.error("update meta error")

    def publish(self, record_id=None):
        r = requests.post(
            url=f"{self.base_url}/deposit/depositions/{record_id}/actions/publish",
            params={"access_token": self.access_token},
        )
        if r.status_code != 202:
            logger.error("publish error")
            return False
        return True
