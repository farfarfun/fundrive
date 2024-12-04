import json
import os

import requests
from funutil import getLogger

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


class ZenodoClient(object):
    """
    https://developers.zenodo.org/
    """

    def __init__(self, access_token, sandbox=False):
        self.access_token = access_token
        self.base_url = (
            "https://sandbox.zenodo.org" if sandbox else "https://zenodo.org"
        )

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
        r = self.__request("post", uri, data=json.dumps(data), headers=headers)
        if r.status_code != 201:
            logger.error(
                f"Error in creation, status code: {r.status_code}   {r.json()['message']}"
            )

        return r.json()

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
        r = self.__request(
            "put",
            uri,
            params={"access_token": self.access_token},
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )
        if r.status_code != 200:
            logger.error(
                f"update meta error,status code: {r.status_code}:{code_list.get(r.status_code)}"
            )
        return r.json()

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
        r = self.__request("post", uri=uri, data=data, files=files)
        if r.status_code != 201:
            logger.error(
                f"Error in data upload, status code: {r.status_code}:{code_list.get(r.status_code)}   {r.json()['message']}"
            )
        return r.json()

    def deposition_files_sort(self, record_id, data):
        uri = f"api/deposit/depositions/{record_id}/files"
        headers = {"Content-Type": "application/json"}
        return self.__request("put", uri=uri, data=json.dumps(data), headers=headers)

    def deposition_files_retrieve(self, record_id, file_id):
        uri = f"api/deposit/depositions/{record_id}/files/{file_id}"
        r = self.__request(
            "get",
            uri=uri,
        )
        return r.json()

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
        r = self.__request(
            "post",
            uri=uri,
        )
        if r.status_code != 202:
            logger.error(
                f"publish error,status code: {r.status_code}:{code_list.get(r.status_code)}"
            )
            return r.json()

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

    def records_list(
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

    def records_retrieve(self, record_id):
        uri = f"api/records/{record_id}"
        r = self.__request("get", uri=uri, params={})
        return r.json()
