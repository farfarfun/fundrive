import json
import os

import requests


class ZenodoClient(object):
    """
    https://developers.zenodo.org/
    """

    base_url = "https://zenodo.org"

    def __init__(self, access_token):
        self.access_token = access_token

    def __request(self, method, uri, params=None, *args, **kwargs):
        url = f"{self.base_url}/{uri}"
        params = params or {"access_token": self.access_token}
        return requests.request(method, url, params=params, *args, **kwargs)

    def representation_list(
        self, q, status=None, sort=None, page=None, size=None, all_versions=None
    ):
        """
        q        string	optional	Search query (using Elasticsearch query string syntax - note that some characters have special meaning here, including /, which is also present in full DOIs).
        status        string	optional	Filter result based on deposit status (either draft or published)
        sort        string	optional	Sort order (bestmatch or mostrecent). Prefix with minus to change form ascending to descending (e.g. -mostrecent).
        page        integer	optional	Page number for pagination.
        size        integer	optional	Number of results to return per page.
        all_versions        integer/string	optional	Show (true or 1) or hide (false or 0) all versions of deposits.
        Returns:
        """
        uri = "/api/deposit/depositions"
        params = {
            "q": q,
            "status": status,
            "sort": sort,
            "page": page,
            "size": size,
            "all_versions": all_versions,
            "access_token": self.access_token,
        }
        return self.__request("get", uri, params=params)

    def representation_create(
        self,
    ):
        uri = "/api/deposit/depositions"
        data = {}
        headers = {"Content-Type": "application/json"}
        return self.__request("post", uri, data=json.dumps(data), headers=headers)

    def representation_retrieve(self, record_id):
        uri = f"/api/deposit/depositions/{record_id}"
        return self.__request(
            "get",
            uri,
        )

    def representation_update(
        self,
        record_id,
        title,
        description,
        names="farfarfun",
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
        uri = f"/api/deposit/depositions/{record_id}"
        return self.__request(
            "put",
            uri,
            params={"access_token": self.access_token},
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )

    def representation_delete(self, record_id):
        uri = f"/api/deposit/depositions/{record_id}"
        return self.__request(
            "delete",
            uri,
        )

    def deposition_files_list(self, record_id):
        uri = f"api/deposit/depositions/{record_id}/files"
        return self.__request(
            "get",
            uri=uri,
        )

    def deposition_files_create(self, record_id, filepath, filename=None):
        uri = f"api/deposit/depositions/{record_id}/files"
        data = {"name": filename or os.path.basename(filepath)}
        files = {"file": open(filepath, "rb")}
        return self.__request("post", uri=uri, data=data, files=files)

    def deposition_files_sort(self, record_id, data):
        uri = f"api/deposit/depositions/{record_id}/files"
        headers = {"Content-Type": "application/json"}
        return self.__request("put", uri=uri, data=json.dumps(data), headers=headers)

    def deposition_files_retrieve(self, record_id, file_id):
        uri = f"api/deposit/depositions/{record_id}/files/{file_id}"
        return self.__request(
            "get",
            uri=uri,
        )

    def deposition_files_update(self, record_id, filename=None):
        uri = f"api/deposit/depositions/{record_id}/files"
        data = {"name": filename}
        headers = {"Content-Type": "application/json"}
        return self.__request("put", uri=uri, data=data, headers=headers)

    def deposition_files_delete(self, record_id, file_id):
        uri = f"api/deposit/depositions/{record_id}/files/{file_id}"
        return self.__request(
            "delete",
            uri=uri,
        )

    def deposition_actions_publish(self, record_id):
        uri = f"api/deposit/depositions/{record_id}/actions/publish"
        return self.__request(
            "post",
            uri=uri,
        )

    def deposition_actions_edit(self, record_id):
        uri = f"api/deposit/depositions/{record_id}/actions/edit"
        return self.__request(
            "post",
            uri=uri,
        )

    def deposition_actions_discard(self, record_id):
        uri = f"api/deposit/depositions/{record_id}/actions/discard"
        return self.__request(
            "post",
            uri=uri,
        )

    def deposition_actions_new_version(self, record_id):
        uri = f"api/deposit/depositions/{record_id}/actions/newversion"
        return self.__request(
            "post",
            uri=uri,
        )
