import logging

import requests
from funsecret import read_secret

logger = logging.getLogger("tikhub")

"""
https://api.tikhub.io/docs
"""


class TikHubAPI:
    def __init__(self, timeout=10):
        self.domain = "https://api.tikhub.io"
        self.timeout = timeout
        self.token: str = ...
        self._headers: dict = ...

    def login(self, username=None, password=None, token=None) -> bool:
        if token is not None:
            self.token = token
            read_secret(
                cate1="fundrive", cate2="tiktok", cate3="token", value=self.token
            )
        elif username is not None and password is not None:
            token_expiry_minutes: int = 525600
            url = (
                f"{self.domain}/user/login?token_expiry_minutes={token_expiry_minutes}"
            )

            payload = {"username": username, "password": password}
            response = requests.request("POST", url, data=payload).json()
            self.token = response.get("access_token")
            read_secret(
                cate1="fundrive", cate2="tiktok", cate3="token", value=self.token
            )
            logger.info(
                f"Your token is: {(response.get('access_token', response.get('detail')))}"
            )
        else:
            self.token = read_secret(cate1="fundrive", cate2="tiktok", cate3="token")

        self._headers = {
            "Cookie": f"Authorization={self.token}",
            "Authorization": f"Bearer {self.token}",
        }
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
        return self._get(uri="promotion/claim/", params=data)

    def promotion_daily_check_in(self):
        return self._get(uri="promotion/daily_check_in/")


class DouyinTikHubApi(TikHubAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_douyin_video_data(
        self, url: str = None, video_id: str = None, language="zh"
    ) -> dict:
        """
        解析单一抖音视频数据
        """
        data = {"douyin_video_url": url, "video_id": video_id, "language": language}
        return self._get(uri="douyin/video_data/", params=data)

    def get_douyin_user_data(
        self, url: str = None, user_id: str = None, language="zh"
    ) -> dict:
        """
        解析抖音作者数据
        """
        data = {"douyin_user_url": url, "sec_user_id": user_id, "language": language}
        return self._get(uri="douyin/user_data/", params=data)

    def get_douyin_user_profile_videos_data(
        self,
        url: str = None,
        user_id: str = None,
        max_cursor=0,
        min_cursor=0,
        count=20,
        language="zh",
    ) -> dict:
        """
        解析抖音作者数据
        """
        data = {
            "douyin_user_url": url,
            "sec_user_id": user_id,
            "max_cursor": max_cursor,
            "min_cursor": min_cursor,
            "language": language,
            "count": count,
        }
        return self._get(uri="douyin/user_data/", params=data)


class TikTokTikHubApi(TikHubAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_tiktok_video_data(
        self, url: str = None, video_id: str = None, region="US", language="en"
    ) -> dict:
        """
        解析TikTok视频
        """
        data = {
            "tiktok_video_url": url,
            "video_id": video_id,
            "region": region,
            "language": language,
        }
        return self._get(uri=f"/tiktok/video_data/", params=data)


class XiaohongshuHubApi(TikHubAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_xhs_note_data(self, url: str = None, note_id: str = None) -> dict:
        """
        解析小红书笔记数据。
        :param url: 小红书笔记链接
        :param note_id: 小红书笔记ID
        优先使用note_id，如果没有note_id则使用url, 两个参数二选一。
        :return:
            {
              "status": true,
              "platform": "string",
              "endpoint": "string",
              "total_time": 0,
              "message": "string",
              "next_url": "string",
              "data": {}
            }
        """
        data = {
            "url": url,
            "note_id": note_id,
        }
        return self._get(uri="/xhs/get_note_data/", params=data)

    def get_xhs_user_info(self, user_id) -> dict:
        """
        解析小红书用户数据。
        :param user_id: 用户ID
        :return:
            {
              "status": true,
              "platform": "string",
              "endpoint": "string",
              "total_time": 0,
              "message": "string",
              "next_url": "string",
              "data": {}
            }
        """
        data = {"user_id": user_id}
        return self._get(uri="/xhs/get_user_info/", params=data)

    def get_xhs_user_notes(self, user_id, cursor=None, num=10) -> dict:
        """
        解析小红书用户笔记数据。
        :param user_id: 用户ID
        :param cursor: 游标(从返回数据中获取)
        :param num: 数量
        :return:
            {
              "status": true,
              "platform": "string",
              "endpoint": "string",
              "total_time": 0,
              "message": "string",
              "next_url": "string",
              "data": {}
            }
        """
        data = {"user_id": user_id, "cursor": cursor, "num": num}
        return self._get(uri="/xhs/get_user_notes/", params=data)

    def get_xhs_note_comments(self, note_id, cursor=None, num=10) -> dict:
        """

        :param note_id:
        :param cursor:
        :param num:
        :return:
            {
              "status": true,
              "platform": "string",
              "endpoint": "string",
              "total_time": 0,
              "message": "string",
              "next_url": "string",
              "data": {}
            }
        """
        data = {"user_id": note_id, "cursor": cursor, "num": num}
        return self._get(uri="/xhs/get_note_comments/", params=data)

    def get_xhs_note_sub_comments(
        self, note_id, root_comment_id, cursor=None, num=10
    ) -> dict:
        """

        :param note_id:
        :param root_comment_id:
        :param cursor:
        :param num:
        :return:
            {
              "status": true,
              "platform": "string",
              "endpoint": "string",
              "total_time": 0,
              "message": "string",
              "next_url": "string",
              "data": {}
            }
        """
        data = {
            "user_id": note_id,
            "root_comment_id": root_comment_id,
            "cursor": cursor,
            "num": num,
        }
        return self._get(uri="/xhs/get_note_sub_comments/", params=data)


class WeiboHubApi(TikHubAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_weibo_user_info(self, user_id) -> dict:
        """
        解析微博用户信息数据。
        :param user_id: 用户ID/User ID
        :return:
            {
              "status": true,
              "platform": "string",
              "endpoint": "string",
              "total_time": 0,
              "message": "string",
              "next_url": "string",
              "data": {}
            }
        """
        data = {"user_id": user_id}
        return self._get(uri="/weibo/get_user_info/", params=data)

    def get_weibo_user_posts(self, user_id, page=1, feature=None) -> dict:
        """
        解析微博用户发布的微博数据
        :param user_id: 用户ID/User ID
        :param page: 页数/Page
        :param feature: 0-全部 1-原创 2-图片 3-视频 4-音乐 5-商品 6-链接 7-投票
        :return:
            {
              "status": true,
              "platform": "string",
              "endpoint": "string",
              "total_time": 0,
              "message": "string",
              "next_url": "string",
              "data": {}
            }
        """
        data = {"user_id": user_id, "page": page, "feature": feature}
        return self._get(uri="/weibo/get_user_posts/", params=data)


def test1():
    douyin = DouyinTikHubApi()

    douyin.login()
    print(douyin.user_me())
    # print(tikhub.parse_douyin_video("https://www.douyin.com/video/7153585499477757192"))
    print(douyin.get_douyin_video_data(video_id="7153585499477757192"))

    tiktok = TikTokTikHubApi()
    tiktok.login()
    print(
        tiktok.get_tiktok_video_data(
            "https://www.tiktok.com/@evil0ctal/video/7202594778217844014"
        )
    )


# test1()
