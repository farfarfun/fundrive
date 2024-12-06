import os
from typing import List

from fundrive.core import BaseDrive, DriveFile
from funget import simple_download
from funsecret import read_secret
from funutil import getLogger
from funutil.cache import cache
from .client import ZenodoClient

logger = getLogger("fundrive")


class ZenodoDrive(BaseDrive):
    def __init__(self):
        super().__init__()
        self.access_token = None

        self.client = ZenodoClient(access_token=self.access_token)

    def check_token(self):
        if not isinstance(self.access_token, str) or not self.access_token:
            logger.error("Token need to be a string")
        return self.client.representation_create()[0]

    def login(self, access_token=None, *args, **kwargs) -> bool:
        self.access_token = access_token or read_secret(
            "fundrive", "zenodo", "access_token"
        )
        self.client.access_token = self.access_token
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
        return self.client.records_list(
            q=q,
            status=status,
            sort=sort,
            page=page,
            size=size,
            all_versions=all_versions,
            communities=communities,
            type=type,
            subtype=subtype,
            bounds=bounds,
            custom=custom,
            *args,
            **kwargs,
        )[1]

    @cache
    def get_dir_list(self, q=None, *args, **kwargs) -> List[DriveFile]:
        response = self.search_records(q=q, *args, **kwargs)
        result = []
        for record in response["hits"]["hits"]:
            result.append(DriveFile(fid=record["id"], name=record["title"], **record))
        return result

    @cache
    def get_file_info(
        self, fid=None, record_id=None, filepath=None, *args, **kwargs
    ) -> DriveFile:
        response = self.client.deposition_files_retrieve(
            record_id=record_id, file_id=filepath
        )[1]
        return DriveFile(fid=fid, name=response["key"], **response)

    @cache
    def get_file_list(self, record_id, *args, **kwargs) -> List[DriveFile]:
        response = self.client.records_retrieve(record_id=record_id)[1]
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
        return self.client.representation_create()[1]

    def upload_dir(
        self,
        local_path,
        record_id=None,
        recursion=True,
        overwrite=False,
        check=True,
        *args,
        **kwargs,
    ) -> bool:
        if check:
            record_id = self.check_record(record_id=record_id)

        for file in os.listdir(local_path):
            file_path = os.path.join(local_path, file)
            if os.path.isfile(file_path):
                self.upload_file(
                    local_path=file_path,
                    record_id=record_id,
                    overwrite=overwrite,
                    check=False,
                )
            elif os.path.isdir(file_path) and recursion:
                self.upload_dir(
                    local_path=file_path,
                    record_id=record_id,
                    overwrite=overwrite,
                    check=False,
                )
        return True

    def upload_file(
        self,
        local_path,
        record_id=None,
        recursion=True,
        overwrite=False,
        check=True,
        *args,
        **kwargs,
    ) -> bool:
        if check:
            record_id = self.check_record(record_id, new_version=False)
        return self.client.deposition_files_upload(
            record_id=record_id, filepath=local_path
        )[0]

    def check_record(self, record_id=None, new_version=True, *args, **kwargs) -> int:
        if self.client.records_retrieve(record_id)[0] is False:
            return record_id
        if new_version:
            response = self.client.deposition_actions_new_version(record_id=record_id)
            if response[0]:
                return response[1]["id"]
        raise Exception(f"No record found for {record_id}")

    def publish(
        self,
        record_id=None,
        title="My first upload",
        description="My first upload",
        names="fundrive",
        creators=None,
    ):
        self.client.representation_update(
            record_id=record_id,
            title=title,
            description=description,
            names=names,
            creators=creators,
        )
        return self.client.deposition_actions_publish(record_id=record_id)[1]
