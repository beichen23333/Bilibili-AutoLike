from .video import BiliVideo
from .Action.video_action import VideoActionMixin
from .Action.reply_action import ReplyActionMixin
from .Action.AI.ai_action import AIActionMixin

class BiliAction(BiliVideo, VideoActionMixin, ReplyActionMixin, AIActionMixin):
    async def close(self):
        await self.client.aclose()
