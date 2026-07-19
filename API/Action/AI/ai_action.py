from .ai_client import BiliAIClient
from ...config import Config

class AIActionMixin:
    async def get_ai_reply(self, dialogue_context: list, target_user: str) -> str:
        """
        解析评论区上下文，并调用独立 AI 客户端生成回复
        
        :param dialogue_context: 经过格式化后的评论区对话历史上下文列表
        :param target_user: 触发回复的目标用户名
        :return: AI 生成的回复文本
        """
        if not self.DeepSeekAPI:
            return "错误：未配置 DEEPSEEK_API_KEY 环境变量"

        context_text = "【当前评论区的对话如下】：\n"
        for turn in dialogue_context:
            if turn['is_root']:
                context_text += f"楼主 [{turn['user']}]: {turn['content']}\n"
            elif turn['reply_to_user']:
                context_text += f"  └─ 用户 [{turn['user']}] 回复了 [{turn['reply_to_user']}]: {turn['content']}\n"
            else:
                context_text += f"  └─ 用户 [{turn['user']}]: {turn['content']}\n"

        user_content = f"{context_text}\n请根据以上上下文，以挽樱的身份直接生成一句回复（直接回复对方即可，注意你对他的称呼是“老师”）："

        ai_client = BiliAIClient(api_key=self.DeepSeekAPI)

        return await ai_client.generate_reply(self.client, user_content)
