"""
https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28
"""

import base64
from typing import Any, Dict, List

import orjson
import requests
from funsecret import read_secret

from fundrive.core import BaseDrive


class GithubDrive(BaseDrive):
    def __init__(self, *args, **kwargs):
        super(GithubDrive, self).__init__(*args, **kwargs)
        self.base_url = "https://api.github.com"
        self.repo_str = None
        self.headers = {}

    def login(self, repo_str, access_tokens=None, *args, **kwargs) -> bool:
        access_tokens = access_tokens or read_secret(
            cate1="fundrive",
            cate2="drives",
            cate3="fungithub",
            cate4="access_tokens",
        )
        self.headers = {"Authorization": f"Token {access_tokens}"}
        self.repo_str = repo_str
        return True

    def delete(self, git_path, *args, **kwargs) -> bool:
        requests.get(
            f"{self.base_url}/repos/{self.repo_str}/contents/{git_path}",
            headers=self.headers,
        )
        return True

    def get_dir_info(self, git_path, *args, **kwargs) -> Dict[str, Any]:
        data = self.get_dir_list(git_path)
        if len(data) > 0:
            return data[0]
        return {}

    def get_file_info(self, git_path, *args, **kwargs) -> Dict[str, Any]:
        res = requests.get(
            f"{self.base_url}/repos/{self.repo_str}/contents/{git_path}",
            headers=self.headers,
        )
        data = res.json()
        if len(data) == 0 or "name" not in data:
            return {}
        return {
            "name": data["name"],
            "path": data["path"],
            "size": data["size"],
            "sha": data["sha"],
            # "time": datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S %Z").strftime("%Y-%m-%d %H:%M:%S"),
        }

    def get_file_list(
        self, git_path, recursive=False, *args, **kwargs
    ) -> List[Dict[str, Any]]:
        all_files = []
        res = requests.get(
            f"{self.base_url}/repos/{self.repo_str}/contents/{git_path}",
            headers=self.headers,
        )
        for data in res.json():
            if data["type"] != "dir":
                all_files.append(
                    {
                        "name": data["name"],
                        "path": data["path"],
                        "size": data["size"],
                        "sha": data["sha"],
                        # "time": datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S %Z").strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
            elif recursive:
                all_files.extend(self.get_file_list(data["path"]))
        return all_files

    def get_dir_list(
        self, git_path, recursive=False, *args, **kwargs
    ) -> List[Dict[str, Any]]:
        all_files = []
        res = requests.get(
            f"{self.base_url}/repos/{self.repo_str}/contents/{git_path}",
            headers=self.headers,
        )
        for data in res.json():
            if data["type"] == "dir":
                all_files.append(
                    {
                        "name": data["name"],
                        "path": data["path"],
                        "size": data["size"],
                        # "time": datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S %Z").strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
                if recursive:
                    all_files.extend(self.get_file_list(data["path"]))
        return all_files

    def upload_file(
        self,
        file_path="./cache",
        content=None,
        git_path=None,
        message="committing files",
        branch="master",
        overwrite=False,
        *args,
        **kwargs,
    ) -> bool:
        uri = f"{self.base_url}/repos/{self.repo_str}/contents/{git_path}"
        if content is None:
            content = open(file_path, "r").read()
        if not isinstance(content, str):
            content = orjson.dumps(content).decode("utf-8")

        data = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode(),
            "branch": branch,
        }
        exist_info = self.get_file_info(git_path)
        if "sha" in exist_info:
            data["sha"] = exist_info["sha"]

        response = requests.put(uri, headers=self.headers, json=data)
        if response.status_code not in (200, 201):
            print(response.status_code, response.text)
        return True
