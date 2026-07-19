import time
import urllib.parse
import traceback
from .action import BiliAction
from .config import Config

class BiliHistory(BiliAction):
    async def start_watch(self, aid: int) -> dict:
        """
        触发视频点击计数
        :param aid: 视频 AID
        """
        return await self._http_post(Config.HISTORY_CLICK_URL, data={"aid": str(aid)})

    async def report_heartbeat(self, bvid: str, aid: int, cid: int, played_time: int, 
                               duration: int, session_id: str, img_key: str, sub_key: str) -> dict:
        """
        上报视频播放心跳数据
        :param played_time: 已播放时长
        :param duration: 视频总时长
        """
        now = int(time.time())
        real_time = played_time if played_time > 0 else duration
        
        # WBI 签名参数组装
        w_params = self._enc_wbi({
            "w_start_ts": now - real_time, "w_mid": 0, "w_aid": aid, "w_dt": 2, 
            "w_realtime": real_time, "w_playedtime": played_time, 
            "w_real_played_time": real_time, "w_video_duration": duration,
            "w_last_play_progress_time": real_time, "web_location": 1315873
        }, img_key, sub_key)

        # 业务数据上报
        data = {
            "aid": str(aid), "bvid": bvid, "cid": str(cid), "epid": "0", "sid": "0", "mid": "0",
            "played_time": str(played_time), "realtime": str(real_time), 
            "real_played_time": str(real_time), "refer_url": f"https://www.bilibili.com/video/{bvid}/",
            "quality": "80", "video_duration": str(duration), "last_play_progress_time": str(real_time),
            "max_play_progress_time": str(real_time), "start_ts": str(now - real_time), 
            "type": "3", "sub_type": "0", "dt": "2", "outer": "0", "spmid": "333.788.0.0",
            "from_spmid": "333.788.0.0", "session": session_id, "csrf": self.csrf,
            "extra": '{"player_version":"4.8.36"}', "play_type": "0" if played_time > 0 else "4"
        }
        
        return await self._http_post(Config.HISTORY_HEARTBEAT_URL, data=data, params=w_params)

    async def report_history(self, aid: int, cid: int, progress: int) -> dict:
        """
        上报视频观看进度（历史记录）
        :param aid: 视频 AID
        :param cid: 视频 CID
        :param progress: 播放进度 (秒)
        """
        data = {
            "aid": str(aid), "cid": str(cid), "progress": str(progress), 
            "platform": "web", "csrf": self.csrf
        }
        return await self._http_post(Config.HISTORY_REPORT_URL, data=data)
