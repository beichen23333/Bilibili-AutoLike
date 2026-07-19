import time
import httpx
from .base import BiliBase
from .config import Config

class BiliLogin(BiliBase):
    async def get_tv_qrcode(self) -> dict:
        """
        获取电视端 (TV) 登录二维码及认证码 (auth_code)
        """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": Config.TV_USER_AGENT,
            "Referer": Config.HOME_URL
        }
        
        qrcode_data = {
            "appkey": Config.TV_APP_KEY, 
            "local_id": 0, 
            "ts": int(time.time())
        }
        qrcode_data["sign"] = self._calc_tv_sign(qrcode_data)

        return await self._http_post(
            Config.TV_QRCODE_URL, 
            data=qrcode_data, 
            headers=headers, 
            caller="BiliLogin.get_tv_qrcode"
        )

    async def poll_tv_login(self, auth_code: str) -> dict:
        """
        轮询电视端 (TV) 二维码的登录状态
        :param auth_code: 获取二维码时返回的特征认证码
        """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": Config.TV_USER_AGENT,
            "Referer": Config.HOME_URL
        }
        
        poll_data = {
            "appkey": Config.TV_APP_KEY, 
            "auth_code": str(auth_code),
            "local_id": 0, 
            "ts": int(time.time())
        }
        poll_data["sign"] = self._calc_tv_sign(poll_data)

        return await self._http_post(
            Config.TV_POLL_URL, 
            data=poll_data, 
            headers=headers, 
            caller="BiliLogin.poll_tv_login"
        )

    async def get_web_qrcode(self) -> dict:
        """
        获取网页端 (Web) 登录二维码及用于轮询的 qrcode_key
        """
        return await self._http_get(
            Config.WEB_QRCODE_URL, 
            caller="BiliLogin.get_web_qrcode"
        )

    async def poll_web_login(self, qrcode_key: str, custom_client: httpx.AsyncClient = None) -> dict:
        """
        轮询网页端 (Web) 二维码的登录状态
        :param qrcode_key: 二维码凭证密钥
        :param custom_client: 可选，客户如果想传入外部的异步 httpx 客户端来隔离 Cookie 容器
        """
        params = {"qrcode_key": str(qrcode_key)}
        
        return await self._http_get(
            Config.WEB_POLL_URL, 
            params=params, 
            custom_client=custom_client, 
            caller="BiliLogin.poll_web_login"
        )
