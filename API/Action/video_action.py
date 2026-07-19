import time
import re
from ..config import Config

class VideoActionMixin:

    async def dislike_video(self, aid: int, dislike: int = 0) -> dict:
        """
        不喜欢/点踩视频（APP 端接口）
        
        :param aid: 视频稿件的 av 号 (Animation ID)
        :param dislike: 操作类型，1 表示点踩，0 表示取消点踩
        :return: 包含响应状态码的字典
        """
        params = {
            "access_key": self.access_token,
            "aid": str(aid),
            "appkey": Config.APP_KEY,
            "dislike": str(dislike),
            "ts": str(int(time.time()))
        }
        params["sign"] = self._calc_sign(params)
        
        return await self._http_post(
            Config.APP_DISLIKE_URL, 
            data=params, 
            headers=self.app_headers, 
            caller="VideoAction.dislike_video"
        )

    async def like_video(self, aid: int) -> dict:
        """
        点赞视频（APP 端接口）
        
        :param aid: 视频稿件的 av 号 (Animation ID)
        :return: 包含响应状态码的字典
        """
        params = {
            "access_key": self.access_token,
            "aid": str(aid),
            "appkey": Config.APP_KEY,
            "like": "0",
            "ts": str(int(time.time()))
        }
        params["sign"] = self._calc_sign(params)
        
        return await self._http_post(
            Config.APP_LIKE_URL, 
            data=params, 
            headers=self.app_headers, 
            caller="VideoAction.like_video"
        )

    async def get_fav_folders(self, up_mid: int) -> dict:
        """
        获取用户创建的所有收藏夹列表
        
        :param up_mid: 目标用户的 UID
        :return: 包含收藏夹列表信息的 JSON 字典
        """
        params = {"up_mid": str(up_mid), "type": "2", "web_location": "333.1387"}
        return await self._http_get(
            Config.FAV_FOLDER_LIST_URL, 
            params=params, 
            caller="VideoAction.get_fav_folders"
        )

    async def add_fav_folder(self, title: str, intro: str = "", cover: str = "", privacy: int = 0) -> dict:
        """
        新建一个视频收藏夹
        
        :param title: 收藏夹标题
        :param intro: 收藏夹简介
        :param cover: 收藏夹封面图片 URL
        :param privacy: 是否加密/私密，0 表示公开，1 表示私密
        :return: 包含新建收藏夹信息的 JSON 字典
        """
        data = {
            "title": str(title), 
            "intro": str(intro), 
            "privacy": str(privacy), 
            "cover": str(cover), 
            "csrf": str(self.csrf)
        }
        return await self._http_post(
            Config.FAV_FOLDER_ADD_URL, 
            data=data, 
            caller="VideoAction.add_fav_folder"
        )

    async def init_fav_folder(self) -> bool:
        """
        初始化收藏夹配置，获取当前登录用户的 UID 并检查或自动匹配可用的空闲收藏夹
        
        :return: 初始化成功返回 True，失败返回 False
        """
        data = await self._http_get(Config.NAV_URL, caller="VideoAction.init_fav_folder")
        
        if data.get("code") == 0 and "data" in data:
            self.my_mid = data["data"]["mid"]
            await self.update_available_folder()
            return self.current_folder_id is not None
            
        return False

    async def update_available_folder(self):
        """
        更新当前可用收藏夹 ID。若已有收藏夹容量满 1000 则自动递增序列并创建新收藏夹（如“收藏1”、“收藏2”）
        """
        res = await self.get_fav_folders(self.my_mid)
        if res.get("code") == 0 and (data := res.get("data")):
            folder_list = data.get("list") or []
            max_num = 0
            for folder in folder_list:
                if not folder:
                    continue
                title = folder.get("title", "")
                match = re.match(r"^收藏(\d+)$", title)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
                    if folder.get("media_count", 0) < 1000:
                        self.current_folder_id = folder.get("id")
                        return
            
            next_num = max_num + 1
            new_title = f"收藏{next_num}"
            default_cover = "https://i1.hdslb.com/bfs/face/44b570b4015a50891e0032d3c79d96a63cee8672.png"
            new_res = await self.add_fav_folder(title=new_title, intro="自动创建", cover=default_cover, privacy=0)
            if new_res.get("code") == 0 and (new_data := new_res.get("data")):
                self.current_folder_id = new_data.get("id")

    async def collect_video(self, rid: int, add_media_ids: str = "", del_media_ids: str = "") -> dict:
        """
        收藏视频或将视频移出收藏夹
        
        :param rid: 视频稿件的 av 号 (aid)
        :param add_media_ids: 需要加入的目标收藏夹 ID 字符串，多个用逗号隔开
        :param del_media_ids: 需要移出的目标收藏夹 ID 字符串，多个用逗号隔开
        :return: 包含响应状态码及提示信息的 JSON 字典
        """
        data = {
            "rid": str(rid), 
            "type": "2", 
            "add_media_ids": str(add_media_ids), 
            "del_media_ids": str(del_media_ids), 
            "csrf": str(self.csrf), 
            "eab_x": "1", 
            "ramval": "0", 
            "ga": "1"
        }
        return await self._http_post(
            Config.FAV_RESOURCE_DEAL_URL, 
            data=data, 
            caller="VideoAction.collect_video"
        )

    async def share_video(self, bvid: str = None, aid: int = None) -> dict:
        """
        分享视频
        
        :param bvid: 视频的 BV 号
        :param aid: 视频的 AV 号（与 bvid 二选一传值即可）
        :return: 包含响应状态码及提示信息的 JSON 字典
        """
        data = {
            "csrf": str(self.csrf), 
            "eab_x": "1", 
            "ramval": "5", 
            "source": "web_normal", 
            "ga": "1"
        }
        if bvid:
            data["bvid"] = str(bvid)
        elif aid:
            data["aid"] = str(aid)
            
        return await self._http_post(
            Config.SHARE_ADD_URL, 
            data=data, 
            caller="VideoAction.share_video"
        )

    async def send_danmaku(self, cid: int, bvid: str, msg: str) -> dict:
        """
        发送视频弹幕
        
        :param cid: 视频分 P 的 cid (Chat ID)
        :param bvid: 视频的 BV 号
        :param msg: 弹幕文本内容
        :return: 包含响应状态码及提示信息的 JSON 字典
        """
        img_key, sub_key = await self.get_wbi_keys()
        query_params = self._enc_wbi({"web_location": "1315873", "csrf": self.csrf}, img_key, sub_key)
        
        form_data = {
            "type": "1", 
            "oid": str(cid), 
            "msg": str(msg), 
            "bvid": str(bvid), 
            "progress": "0",
            "color": "16777215", 
            "fontsize": "25", 
            "pool": "0", 
            "mode": "1",
            "rnd": str(int(time.time() * 1000000)), 
            "csrf": str(self.csrf)
        }
        return await self._http_post(
            Config.DANMAKU_POST_URL, 
            params=query_params, 
            data=form_data, 
            caller="VideoAction.send_danmaku"
        )
