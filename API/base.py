import base64
import hashlib
import random
import string
import time
import traceback
import urllib.parse
from functools import reduce

import httpx

from .config import Config


class BiliBase:
    client = httpx.AsyncClient(
        timeout=Config.TIMEOUT,
        limits=httpx.Limits(
            max_keepalive_connections=Config.MAX_KEEPALIVE_CONNECTIONS,
            max_connections=Config.MAX_CONNECTIONS,
        ),
        http2=True,
    )

    def __init__(
        self,
        access_token: str = None,
        sessdata: str = None,
        bili_jct: str = None,
        DeepSeek: str = None,
    ):
        self.access_token = access_token
        self.csrf = bili_jct

        if DeepSeek:
            self.DeepSeekAPI = DeepSeek

        self.cookies = {}

        if sessdata and bili_jct:
            self.cookies = {"SESSDATA": sessdata, "bili_jct": bili_jct}

        self.web_headers = {
            "User-Agent": Config.DEFAULT_USER_AGENT,
            "Referer": Config.HOME_URL,
            "Origin": Config.HOME_URL,
        }
        self.app_headers = {
            "User-Agent": Config.APP_USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        self._wbi_keys = None

    @staticmethod
    def base64_encode_random_string(min_len: int, max_len: int) -> str:
        """对应 Dart 中的 Utils.base64EncodeRandomString(min, max)"""
        k = random.randint(min_len, max_len)
        rand_str = "".join(random.choices(string.printable, k=k))
        return base64.b64encode(rand_str.encode()).decode().rstrip("=")

    async def init_device_cookies(self) -> bool:
        """初始化必要设备 Cookie (buvid3, buvid4, b_nut)，防 -352 风控必备！"""
        try:
            res = await self.client.get(
                Config.SPI_URL, headers=self.web_headers
            )
            if res.status_code == 200 and (data := res.json()).get("code") == 0:
                if finger_data := data.get("data"):
                    self.cookies["buvid3"] = finger_data.get("b_3")
                    self.cookies["buvid4"] = finger_data.get("b_4")

            res_home = await self.client.get(
                Config.HOME_URL,
                headers=self.web_headers,
                cookies=self.cookies,
            )
            self.cookies["b_nut"] = res_home.cookies.get(
                "b_nut", str(int(time.time()))
            )
            return True
        except Exception as e:
            print(f"[init_device_cookies] 初始化设备Cookie失败: {e}")
            return False

    async def get_wbi_keys(self) -> tuple[str, str]:
        if self._wbi_keys:
            return self._wbi_keys

        try:
            res = await self.client.get(
                Config.NAV_URL, headers=self.web_headers, cookies=self.cookies
            )
            if res.status_code == 200 and (data := res.json()).get("code") == 0:
                wbi_img = data["data"]["wbi_img"]
                img_key = wbi_img["img_url"].rsplit("/", 1)[-1].split(".")[0]
                sub_key = wbi_img["sub_url"].rsplit("/", 1)[-1].split(".")[0]
                self._wbi_keys = (img_key, sub_key)
                return self._wbi_keys
        except Exception as e:
            print(f"[get_wbi_keys] 获取密钥失败: {e}\n{traceback.format_exc()}")

        return Config.WBI_FALLBACK_KEY, Config.WBI_FALLBACK_KEY

    async def _enc_wbi(self, params: dict) -> dict:
        """计算 WBI 签名 (对应 WbiSign.makSign)"""
        try:
            img_key, sub_key = await self.get_wbi_keys()
            orig = img_key + sub_key
            mixin_key = reduce(
                lambda s, i: s + orig[i], Config.WBI_ENC_TAB, ""
            )[:32]

            params_to_sign = dict(params)
            params_to_sign["wts"] = round(time.time())

            cleaned_params = {
                k: "".join(filter(lambda c: c not in "!'()*", str(v)))
                for k, v in sorted(params_to_sign.items())
                if v is not None
            }

            query = urllib.parse.urlencode(cleaned_params)
            cleaned_params["w_rid"] = hashlib.md5(
                (query + mixin_key).encode()
            ).hexdigest()
            return cleaned_params

        except Exception as e:
            print(f"[_enc_wbi] 签名失败: {e}\n{traceback.format_exc()}")
            return params

    async def _http_get(self, url: str, params: dict = None, headers: dict = None, custom_client: httpx.AsyncClient = None, caller: str = "Base") -> dict:
        try:
            active_client = custom_client if isinstance(custom_client, httpx.AsyncClient) else self.client
            active_headers = headers if headers is not None else self.web_headers
        
            response = active_client.get(url, params=params, headers=active_headers, cookies=self.cookies)
            if hasattr(response, "__await__"):
                res = await response
            else:
                res = response

            if res.status_code == 200:
                return res.json()
            if res.status_code == 412:
                print("触发风控。")
#            print(f"[{caller}] 异常状态码: {res.status_code} URL: {url}")
            return {"code": -999, "message": f"HTTP_{res.status_code}"}
        except Exception as e:
#            print(f"[{caller}] GET 网络崩溃! 目标: {url}\n原因: {e}\n{traceback.format_exc()}")
            pass
            return {"code": -999, "message": str(e)}

    async def _http_post(self, url: str, data: dict = None, json: dict = None, params: dict = None, headers: dict = None, custom_client: httpx.AsyncClient = None, caller: str = "Base") -> dict:
        try:
            active_client = custom_client if isinstance(custom_client, httpx.AsyncClient) else self.client
            active_headers = headers if headers is not None else self.web_headers
            
            response = active_client.post(url, data=data, json=json, params=params, headers=active_headers, cookies=self.cookies)
            if hasattr(response, "__await__"):
                res = await response
            else:
                res = response
        
            if res.status_code == 200:
                return res.json()
            if res.status_code == 412:
                print("触发风控。")
#            print(f"[{caller}] 异常状态码: {res.status_code} URL: {url}")
            return {"code": -999, "message": f"HTTP_{res.status_code}"}
        except Exception as e:
#            print(f"[{caller}] POST 网络崩溃! 目标: {url}\n原因: {e}\n{traceback.format_exc()}")
            pass
            return {"code": -999, "message": str(e)}
