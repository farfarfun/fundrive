import base64
import json
from typing import Any, List, Dict

import requests
from fundrive.core import DriveSystem
from funsecret import read_secret


class GiteeDrive(DriveSystem):
    def __init__(self, *args, **kwargs):
        super(GiteeDrive, self).__init__(*args, **kwargs)
        self.base_url = "https://gitee.com/api/v5"
        self.repo_str = None
        self.access_tokens = None

    def login(self, repo_str, access_tokens=None, *args, **kwargs) -> bool:
        if access_tokens:
            read_secret(cate1="fundrive", cate2="drives", cate3="fungitee", cate4="access_tokens", value=access_tokens)
        else:
            access_tokens = read_secret(cate1="fundrive", cate2="drives", cate3="fungitee", cate4="access_tokens")
        self.access_tokens = access_tokens
        self.repo_str = repo_str
        return True

    def get_dir_info(self, git_path, *args, **kwargs) -> Dict[str, Any]:
        data = self.get_dir_list(git_path)
        if len(data) > 0:
            return data[0]
        return {}

    def get_file_info(self, git_path, *args, **kwargs) -> Dict[str, Any]:
        data = {"access_token": self.access_tokens}
        res = requests.get(f"{self.base_url}/repos/{self.repo_str}/contents/{git_path}", data=data)
        data = res.json()
        if len(data) == 0:
            return {}
        return {"name": data["name"], "path": data["path"], "size": data["size"], "sha": data["sha"]}

    def get_file_list(self, git_path, recursive=False, *args, **kwargs) -> List[Dict[str, Any]]:
        all_files = []
        data = {"access_token": self.access_tokens}
        res = requests.get(f"{self.base_url}/repos/{self.repo_str}/contents/{git_path}", data=data)
        for data in res.json():
            if data["type"] != "dir":
                all_files.append(
                    {
                        "name": data["name"],
                        "path": data["path"],
                        "size": data["size"],
                    }
                )
            elif recursive:
                all_files.extend(self.get_file_list(data["path"]))
        return all_files

    def get_dir_list(self, git_path, recursive=False, *args, **kwargs) -> List[Dict[str, Any]]:
        all_files = []
        data = {"access_token": self.access_tokens}
        res = requests.get(f"{self.base_url}/repos/{self.repo_str}/contents/{git_path}", data=data)
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
        if content is None:
            content = open(file_path, "r").read()
        if not isinstance(content, str):
            content = json.dumps(content)

        data = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode(),
            "branch": branch,
            "access_token": self.access_tokens,
        }
        info = self.get_file_info(git_path=git_path)
        if len(info) == 0:
            res = requests.post(f"{self.base_url}/repos/{self.repo_str}/contents/{git_path}", json=data)
        else:
            data["sha"] = info["sha"]
            res = requests.put(f"{self.base_url}/repos/{self.repo_str}/contents/{git_path}", json=data)

        return True
