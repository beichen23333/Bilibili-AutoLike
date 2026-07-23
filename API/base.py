import hashlib
import time
import urllib.parse
import httpx
import traceback
import random
import string
import base64
from functools import reduce
from .config import Config

class BiliBase:
    client = httpx.AsyncClient(
        timeout=Config.TIMEOUT,
        limits=httpx.Limits(
            max_keepalive_connections=Config.MAX_KEEPALIVE_CONNECTIONS,
            max_connections=Config.MAX_CONNECTIONS
        ),
        http2=True
    )

    def __init__(self, access_token: str = None, sessdata: str = None, bili_jct: str = None, DeepSeek: str = None):
        """
        初始化 Bilibili 基础请求类，配置凭证与核心请求头
        :param access_token: App 端登录令牌
        :param sessdata: Web 端身份验证 Cookie 核心值
        :param bili_jct: Web 端 CSRF 安全校验特征值
        """
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
            "Origin": Config.HOME_URL
        }
        self.app_headers = {
            "User-Agent": Config.APP_USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        self._wbi_keys = None
        self.my_mid = None
        self.current_folder_id = None

    async def init_device_cookies(self) -> bool:
        """
        初始化并获取设备必要的 buvid3、buvid4 以及游客 b_nut 追踪 Cookie。
        通过捕获一切潜在异常确保即便网络或客户配置错误，主流程也不会雪崩。
        """
        try:
            res = await self.client.get(Config.SPI_URL, headers=self.web_headers)
            if res.status_code == 200 and (data := res.json()).get("code") == 0:
                if finger_data := data.get("data"):
                    self.cookies["b_3"] = finger_data.get("b_3")
                    self.cookies["b_4"] = finger_data.get("b_4")

            res_home = await self.client.get(Config.HOME_URL, headers=self.web_headers, cookies=self.cookies)
            self.cookies["b_nut"] = res_home.cookies.get("b_nut", str(int(time.time())))
            return True

        except Exception as e:
            print(f"[init_device_cookies] 初始化设备Cookie失败！错误原因: {e}")
            print(f"[完整错误信息]:\n{traceback.format_exc()}")
            return False

    def base64_encode_random_string(self, min_len=16, max_len=64):
        length = random.randint(min_len, max_len)
        rand_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=length)).encode("utf-8")
        return base64.b64encode(rand_bytes).decode("utf-8")

    def _internal_md5_sign(self, params: dict, app_sec: str) -> str:
        """
        对传入的字典参数按照键名升序进行 MD5 签名加密
        """
        query = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if v is not None)
        return hashlib.md5(f"{query}{app_sec}".encode("utf-8")).hexdigest()

    def _calc_sign(self, params: dict) -> str:
        """
        计算常规请求所需的 API 签名 (Sign)
        """
        try:
            return self._internal_md5_sign(params, Config.APP_SEC)
        except Exception as e:
            print(f"[_calc_sign] 计算App签名失败: {e}\n{traceback.format_exc()}")
            return ""

    @staticmethod
    def _calc_tv_sign(params: dict) -> str:
        """
        计算 TV 端请求所需的 API 签名 (Sign)
        """
        try:
            query = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if v is not None)
            return hashlib.md5(f"{query}{Config.TV_APP_SEC}".encode('utf-8')).hexdigest()
        except Exception as e:
            print(f"[_calc_tv_sign] 计算TV端签名失败: {e}\n{traceback.format_exc()}")
            return ""

    async def get_wbi_keys(self) -> tuple[str, str]:
        """
        获取 Web 端 WBI 实时动态加密所需的 img_key 和 sub_key。
        若接口挂掉、用户凭证过期等，会自动 fallback 到默认高强度混淆密钥，保证流程不中断。
        """
        if self._wbi_keys:
            return self._wbi_keys
            
        try:
            res = await self.client.get(Config.NAV_URL, headers=self.web_headers, cookies=self.cookies)
            if res.status_code == 200 and (data := res.json()).get("code") == 0:
                wbi_img = data["data"]["wbi_img"]
                img_key = wbi_img["img_url"].rsplit('/', 1)[-1].split('.')[0]
                sub_key = wbi_img["sub_url"].rsplit('/', 1)[-1].split('.')[0]
                self._wbi_keys = (img_key, sub_key)
                return self._wbi_keys
        except Exception as e:
            print(f"[get_wbi_keys] 无法获取最新WBI动态密钥（可能未登录或接口变动）: {e}")
            print(f"[非致命错误堆栈]:\n{traceback.format_exc()}")

        return Config.WBI_FALLBACK_KEY, Config.WBI_FALLBACK_KEY

    def _enc_wbi(self, params: dict, img_key: str, sub_key: str) -> dict:
        """
        为 Web 端 API 请求注入并计算 WBI 防爬虫签名机制。
        对参数进行特殊字符清洗、加入时间戳、打散混淆排序，最后附加 w_rid 校验串。
        """
        try:
            orig = img_key + sub_key
            mixin_key = reduce(lambda s, i: s + orig[i], Config.WBI_ENC_TAB, '')[:32]
            
            params['wts'] = round(time.time())
            cleaned_params = {
                k: ''.join(filter(lambda c: c not in "!'()*", str(v))) 
                for k, v in sorted(params.items()) if v is not None
            }
            
            query = urllib.parse.urlencode(cleaned_params)
            cleaned_params['w_rid'] = hashlib.md5((query + mixin_key).encode()).hexdigest()
            return cleaned_params
            
        except Exception as e:
            print(f"[_enc_wbi] 客户输入参数产生非预期异常，WBI加密失败: {e}")
            print(f"[详细参数堆栈]:\n{traceback.format_exc()}")
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
#            print(f"[{caller}] 异常状态码: {res.status_code} URL: {url}")
        except Exception as e:
#            print(f"[{caller}] GET 网络崩溃! 目标: {url}\n原因: {e}\n{traceback.format_exc()}")
            pass
        return {"code": -999, "message": "network_error"}

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
#            print(f"[{caller}] 异常状态码: {res.status_code} URL: {url}")
            return {"code": -999, "message": f"HTTP_{res.status_code}"}
        except Exception as e:
#            print(f"[{caller}] POST 网络崩溃! 目标: {url}\n原因: {e}\n{traceback.format_exc()}")
            pass
            return {"code": -999, "message": str(e)}
