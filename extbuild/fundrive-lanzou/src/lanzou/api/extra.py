import json

import requests

from lanzou.api.utils import USER_AGENT
from lanzou.debug import logger

timeout = 2


def get_short_url(url: str):
    """短链接生成器"""
    headers = {'User-Agent': USER_AGENT}
    short_url = ""
    try:
        post_data = {"url": url}
        # 10W次/天, https证书过期
        headers["Authorization"] = "Token xxHQfao69Ra9G7EI87mC"
        resp = requests.post("https://www.dwz.lc/api/url/add", json=post_data, headers=headers, timeout=timeout)
        logger.error(resp.text)
        rsp = json.loads(resp.text)
        if rsp:
            short_url = rsp["short"]
    except Exception as e:
        logger.error(f"get_short_url error: e={e}")

    if not short_url:
        try:
            post_data = {"url": url}
            # 10W次/天, https证书过期
            headers["Authorization"] = "Token cH4lpSuC6LgqoDidiqB5"
            resp = requests.post("https://www.ecx.cx/api/url/add", json=post_data, headers=headers, timeout=timeout)
            logger.error(resp.text)
            rsp = json.loads(resp.text)
            if rsp:
                short_url = rsp["short"]
        except Exception as e:
            logger.error(f"get_short_url error: e={e}")

    if not short_url:
        try:
            # https, 国外,速度较慢
            resp = requests.get(f"https://tinyurl.com/api-create.php?url={url}", headers=headers, timeout=timeout)
            logger.error(resp.text)
            if resp.text and len(resp.text) < 32:
                short_url = resp.text
        except Exception as e:
            logger.error(f"get_short_url error: e={e}")

    if not short_url:
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        post_data = {"long_url": url}
        try:
            # 支持https, 国外,速度较慢
            resp = requests.post("http://gg.gg/create", data=post_data, headers=headers, timeout=timeout).text
            logger.error(resp)
            if resp:
                short_url = resp
        except Exception as e:
            logger.error(f"get_short_url2 error: e={e}")

    return short_url


if __name__ == "__main__":
    url = get_short_url("https://github.com/Leon406/lanzou-gui")
    print(url)
