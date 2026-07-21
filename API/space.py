from .base import BiliBase
from .config import Config


class BiliSpace(BiliBase):

    async def search_archive(
        self,
        mid: object,
        pn: int,
        tid: int = 0,
        ps: int = 30,
        keyword: str = None,
        special_type: str = None,
        order: str = "pubdate",
    ) -> dict:
        # 生成随机字符串
        dm_img_str = self.base64_encode_random_string(16, 64)
        dm_cover_img_str = self.base64_encode_random_string(32, 128)

        # 组装待签名字典
        raw_params = {
            "mid": mid,
            "ps": ps,
            "tid": tid,
            "pn": pn,
            "keyword": keyword,
            "special_type": special_type,
            "order": order,
            "platform": "web",
            "web_location": 333.1387,
            "order_avoided": "true",
            "dm_img_list": "[]",
            "dm_img_str": dm_img_str,
            "dm_cover_img_str": dm_cover_img_str,
            "dm_img_inter": '{"ds":[],"wh":[0,0,0],"of":[0,0,0]}',
        }

        # 过滤值为 None 的字段
        raw_params = {k: v for k, v in raw_params.items() if v is not None}

        # 计算 WBI 签名
        signed_params = await self._enc_wbi(raw_params)

        # 组装 Headers
        space_headers = {
            "User-Agent": Config.DEFAULT_USER_AGENT,
            "Referer": f"https://space.bilibili.com/{mid}",
            "Origin": "https://space.bilibili.com",
        }

        return await self._http_get(
            Config.SPACE_SEARCH_URL, params=signed_params, headers=space_headers, caller="search_archive"
        )
