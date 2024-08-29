import logging

import requests
from funsecret import read_secret

logger = logging.getLogger("fundrive")


class TikHubAPI:
    def __init__(self, timeout=10):
        self.domain = "https://api.tikhub.io"
        self.timeout = timeout
        self.token: str = ...
        self._headers: dict = ...

    def login(self, username=None, password=None, token=None) -> bool:
        if token is not None:
            self.token = token
            read_secret(cate1="fundrive", cate2="tiktok", cate3="token", value=self.token)
        elif username is not None and password is not None:
            token_expiry_minutes: int = 525600
            url = f"{self.domain}/user/login?token_expiry_minutes={token_expiry_minutes}"

            payload = {"username": username, "password": password}
            response = requests.request("POST", url, data=payload).json()
            self.token = response.get("access_token")
            read_secret(cate1="fundrive", cate2="tiktok", cate3="token", value=self.token)
            logger.info(f"Your token is: {(response.get('access_token', response.get('detail')))}")
        else:
            self.token = read_secret(cate1="fundrive", cate2="tiktok", cate3="token")

        self._headers = {"Cookie": f"Authorization={self.token}", "Authorization": f"Bearer {self.token}"}
        return True

    def _get(self, uri, params=None) -> dict:
        url = f"{self.domain}/{uri}"

        try:
            response = requests.get(url, headers=self._headers, params=params)
            return response.json()
        except Exception as e:
            return {"status": False, "msg": e}

    def user_me(self):
        return self._get(uri="users/me/")

    def promotion_claim(self, promotion_id):
        data = {"promotion_id": promotion_id}
        return self._get(uri="promotion/claim", data=data)

    def promotion_daily_check_in(self):
        return self._get(uri="promotion/daily_check_in")

    def parse_douyin_video(self, url: str = None, video_id: str = None, language="zh") -> dict:
        """
        解析抖音视频
        """
        uri = "douyin/video_data/"
        # uri = f"douyin/video_data?douyin_video_url={url}"
        # uri = f"douyin/video_data?video_id={video_id}"
        data = {"douyin_video_url": url, "video_id": video_id}
        return self._get(uri=uri, params=data)

    def parse_tiktok_video(self, url: str) -> dict:
        """
        解析TikTok视频
        """
        return self._get(uri=f"/tiktok/video_data/?tiktok_video_url={url}")


def test1():
    tikhub = TikHubAPI()
    tikhub.login()
    print(tikhub.user_me())
    # print(tikhub.parse_douyin_video("https://www.douyin.com/video/7153585499477757192"))
    print(tikhub.parse_douyin_video(video_id="7153585499477757192"))
    print(tikhub.parse_tiktok_video("https://www.tiktok.com/@evil0ctal/video/7202594778217844014"))


test1()
