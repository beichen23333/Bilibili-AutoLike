import traceback
from .login import BiliLogin
from .config import Config

class BiliVideo(BiliLogin):
    async def get_latest_videos(self) -> list:
        """
        获取全站最新的视频列表（默认获取分区编号0，即全分区的20条最新数据）
        """
        res_json = await self._http_get(
            Config.VIDEO_NEWLIST_URL, 
            params={"rid": "0", "pn": "1", "ps": "20"}
        )
        
        return res_json.get("data", {}).get("archives") or []

    async def get_relation(self, mid: int) -> dict:
        """
        查询当前登录账户与指定用户 (MID) 的社交关系（关注、黑名单等）
        :param mid: 目标用户的唯一 B 站数字 UID
        """
        return await self._http_get(Config.VIDEO_RELATION_URL, params={"mid": str(mid)})

    async def get_video_info(self, bvid: str) -> dict:
        """
        根据视频的 BV 号获取视频的核心基础信息（包含 aid, cid 以及总时长）
        :param bvid: 视频的 BV 字符串
        """
        res_json = await self._http_get(Config.VIDEO_VIEW_URL, params={"bvid": str(bvid).strip()})
        
        try:
            if res_json.get("code") == 0 and (archive_info := res_json.get("data")):
                return {
                    "aid": archive_info.get("aid"),
                    "cid": archive_info.get("cid"),
                    "duration": archive_info.get("duration")
                }
        except Exception as e:
            print(f"[get_video_info] 解析视频详情字典发生未知异常: {e}\n{traceback.format_exc()}")
        return {"aid": None, "cid": None, "duration": 0}
