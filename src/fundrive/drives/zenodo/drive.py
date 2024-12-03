import json
import os
from typing import List

import requests
from funget import simple_download
from funsecret import read_secret
from funutil import getLogger

from fundrive.core import BaseDrive, DriveFile

logger = getLogger("fundrive")
code_list = {
    200: {
        "code": 200,
        "name": "OK",
        "desc": "Request succeeded. Response included. Usually sent for GET/PUT/PATCH requests.",
    },
    201: {
        "code": 201,
        "name": "Created",
        "desc": "Request succeeded. Response included. Usually sent for POST requests.",
    },
    202: {
        "code": 202,
        "name": "Accepted",
        "desc": "Request succeeded. Response included. Usually sent for POST requests, where background processing is needed to fulfill the request.",
    },
    204: {
        "code": 204,
        "name": "No Content",
        "desc": "Request succeeded. No response included. Usually sent for DELETE requests.",
    },
    400: {
        "code": 400,
        "name": "Bad Request",
        "desc": "Request failed. Error response included.",
    },
    401: {
        "code": 401,
        "name": "Unauthorized",
        "desc": "Request failed, due to an invalid access token. Error response included.",
    },
    403: {
        "code": 403,
        "name": "Forbidden",
        "desc": "Request failed, due to missing authorization (e.g. deleting an already submitted upload or missing scopes for your access token). Error response included.",
    },
    404: {
        "code": 404,
        "name": "Not Found",
        "desc": "Request failed, due to the resource not being found. Error response included.",
    },
    405: {
        "code": 405,
        "name": "Method Not Allowed",
        "desc": "Request failed, due to unsupported HTTP method. Error response included.",
    },
    409: {
        "code": 409,
        "name": "Conflict",
        "desc": "Request failed, due to the current state of the resource (e.g. edit a deopsition which is not fully integrated). Error response included.",
    },
    415: {
        "code": 415,
        "name": "Unsupported Media Type",
        "desc": "Request failed, due to missing or invalid request header Content-Type. Error response included.",
    },
    429: {
        "code": 429,
        "name": "Too Many Requests",
        "desc": "Request failed, due to rate limiting. Error response included.",
    },
    500: {
        "code": 500,
        "name": "Internal Server Error",
        "desc": "Request failed, due to an internal server error. Error response NOT included. Don’t worry, Zenodo admins have been notified and will be dealing with the problem ASAP.",
    },
}


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
                f"Token accept error, status code: {r.status_code}:{code_list.get(r.status_code)}  {r.json()['message']}"
            )
        logger.success("access token success")

    def login(self, access_token=None, *args, **kwargs) -> bool:
        self.access_token = access_token or read_secret(
            "fundrive", "zenodo", "access_token"
        )
        return True

    def search_records(
        self,
        q=None,
        status=None,
        sort=None,
        page=None,
        size=None,
        all_versions=None,
        communities=None,
        type=None,
        subtype=None,
        bounds=None,
        custom=None,
        *args,
        **kwargs,
    ):
        """
        q
        string	optional	Search query (using Elasticsearch query string syntax - note that some characters have special meaning here, including /, which is also present in full DOIs).
        status
        string	optional	Filter result based on the deposit status (either draft or published)
        sort
        string	optional	Sort order (bestmatch or mostrecent). Prefix with minus to change form ascending to descending (e.g. -mostrecent).
        page
        integer	optional	Page number for pagination.
        size
        integer	optional	Number of results to return per page.
        all_versions
        integer/string	optional	Show (true or 1) or hide (false or 0) all versions of records.
        communities
        string	optional	Return records that are part of the specified communities. (Use of community identifier)
        type
        string	optional	Return records of the specified type. (Publication, Poster, Presentation…)
        subtype
        string	optional	Return records of the specified subtype. (Journal article, Preprint, Proposal…)
        bounds
        string	optional	Return records filtered by a geolocation bounding box. (Format bounds=143.37158,-38.99357,146.90918,-37.35269)
        custom
        string	optional	Return records containing the specified custom keywords. (Format custom=[field_name]:field_value)

        Returns:

        """
        payload = {
            "q": q,
            "status": status,
            "sort": sort,
            "page": page,
            "size": size,
            "all_versions": all_versions,
            "communities": communities,
            "type": type,
            "subtype": subtype,
            "bounds": bounds,
            "custom": custom,
        }
        r = requests.get(
            url=f"{self.base_url}/records",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        if r.status_code != 200:
            logger.error(
                f"search error, status code: {r.status_code}   {r.json()['message']}"
            )
        return r.json()

    def get_dir_list(self, q=None, *args, **kwargs) -> List[DriveFile]:
        response = self.search_records(q=q, *args, **kwargs)
        result = []
        for record in response["hits"]["hits"]:
            result.append(DriveFile(fid=record["id"], name=record["title"], **record))
        return result

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
        result = []
        for file in response["files"]:
            result.append(
                DriveFile(
                    fid=file["links"]["self"].rstrip("/content"),
                    path=file["key"],
                    name=file["key"],
                    size=file["size"],
                    url=file["links"]["self"],
                    id=file["id"],
                    checksum=file["checksum"],
                )
            )
        return result

    def download_file(
        self, record_id, local_dir, overwrite=False, *args, **kwargs
    ) -> bool:
        for file in self.get_file_list(record_id, *args, **kwargs):
            simple_download(url=file["url"], filepath=f"{local_dir}/{file['name']}")
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
        return r.json()

    def upload_dir(
        self,
        local_path,
        record_id=None,
        bucket_url=None,
        recursion=True,
        overwrite=False,
        *args,
        **kwargs,
    ) -> bool:
        for file in os.listdir(local_path):
            file_path = os.path.join(local_path, file)
            if os.path.isfile(file_path):
                self.upload_file(
                    local_path=file_path,
                    record_id=record_id,
                    bucket_url=bucket_url,
                    overwrite=overwrite,
                )
            elif os.path.isdir(file_path) and recursion:
                self.upload_dir(
                    local_path=file_path,
                    record_id=record_id,
                    bucket_url=bucket_url,
                    overwrite=overwrite,
                )
        return True

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
                    f"Error in data upload, status code: {r.status_code}:{code_list.get(r.status_code)}   {r.json()['message']}"
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
            if r.status_code != 200:
                logger.error(
                    f"upload error, status code: {r.status_code}:{code_list.get(r.status_code)}   {r.json()['message']}"
                )
            else:
                logger.success(
                    f"upload success, status code: {r.status_code}:{code_list.get(r.status_code)}   {r.json()['message']}"
                )
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
            logger.error(
                f"update meta error,status code: {r.status_code}:{code_list.get(r.status_code)}"
            )

    def publish(self, record_id=None):
        r = requests.post(
            url=f"{self.base_url}/deposit/depositions/{record_id}/actions/publish",
            params={"access_token": self.access_token},
        )
        if r.status_code != 202:
            logger.error(
                f"publish error,status code: {r.status_code}:{code_list.get(r.status_code)}"
            )
            return False
        return True
