from ..config import Config

class ReplyActionMixin:

    async def add_reply(self, oid, message: str, r_type: int = 1, plat: int = 1, root_id=None, parent_id=None) -> dict:
        """
        发表评论或回复已有评论
        
        :param oid: 目标业务对象的 ID（如视频的 aid、动态的 id）
        :param message: 评论文本内容
        :param r_type: 评论区类型（1 为视频评论区，11 为动态评论区）
        :param plat: 发布平台（1 为 Web端）
        :param root_id: 根评论的 rpid（若回复二级评论或在某条评论下盖楼，需传此项）
        :param parent_id: 被回复的目标评论的 rpid（若不传或为 0，则默认同 root_id）
        :return: 包含响应状态码及评论详情数据的 JSON 字典
        """
        # 参数清洗强转，防止客户端传入其他类型导致上报或签名失败
        data = {
            "type": str(r_type), 
            "oid": str(oid), 
            "message": str(message), 
            "plat": str(plat), 
            "csrf": str(self.csrf)
        }
        
        if root_id:
            data["root"] = str(root_id)
            # 合并精简 parent 字段分配逻辑
            data["parent"] = str(root_id) if not parent_id or str(parent_id) == "0" else str(parent_id)
            
        # 丢给基类统一的 POST 总网关，告知调用者身份
        return await self._http_post(Config.REPLY_ADD_URL, data=data, caller="ReplyAction.add_reply")

    async def action_reply(self, oid: int, rpid: int, action: int = 1, r_type: int = 1) -> dict:
        """
        对评论进行操作（点赞/点踩）
        
        :param oid: 目标业务对象的 ID（如视频的 aid）
        :param rpid: 目标评论的 ID (Reply ID)
        :param action: 操作代码（1 为点赞，0 为取消点赞，2 为点踩，3 为取消点踩）
        :param r_type: 评论区类型
        :return: 包含响应状态码的 JSON 字典
        """
        data = {
            "type": str(r_type), 
            "oid": str(oid), 
            "rpid": str(rpid), 
            "action": str(action), 
            "csrf": str(self.csrf)
        }
        return await self._http_post(Config.REPLY_ACTION_URL, data=data, caller="ReplyAction.action_reply")

    async def get_unread_replies(self) -> list:
        """
        获取当前账号下最新未读的评论/回复通知消息列表
        
        :return: 解析格式化后的未读评论消息列表。出错或无数据时返回空列表 `[]`
        """
        data = await self._http_get(Config.REPLY_MSG_FEED_URL, caller="ReplyAction.get_unread_replies")

        reply_data = data.get("data", {})
        last_view_at = reply_data.get("last_view_at", 0)
        items = reply_data.get("items")
        
        results = []
        for item in items:
#            if 0 == 0:
            if item and item.get("reply_time", 0) > last_view_at:
                info = item.get("item", {})
                business_type = info.get("business")
                oid = str(info.get("subject_id"))
                type_code = 1

                if business_type == "动态":
                    root_id = str(info.get("source_id"))
                    type_code = 11
                elif business_type == "视频":
                    root_id = str(info.get("source_id"))
                elif business_type == "评论":
                    root_id = str(info.get("root_id"))
                else:
                    print(f"[get_unread_replies] 遇到未识别的业务通知类型: {business_type}")
                    oid = None
                    root_id = None

                results.append({
                    "type": business_type,
                    "type_code": type_code,
                    "user": item.get("user", {}).get("nickname"),
                    "root_content": info.get("root_reply_content"),
                    "source_content": info.get("source_content"),
                    "target_content": info.get("target_reply_content"),
                    "native_uri": info.get("native_uri", ""),
                    "oid": oid,
                    "root_id": root_id,
                    "is_multi": item.get("is_multi"),
                    "counts": item.get("counts")
                })
        return results

    async def get_reply_details(self, oid: str, root_id: str, type_code: int = 1) -> list:
        """
        获取某条根评论下的子评论对话树明细
        
        :param oid: 目标业务对象的 ID
        :param root_id: 根评论的 rpid
        :param type_code: 评论区类型（1 为视频，11 为动态）
        :return: 格式化后的树状对话上下文列表。出错或无数据时返回空列表 `[]`
        """
        params = {
            "type": str(type_code), 
            "oid": str(oid), 
            "root": str(root_id), 
            "ps": "20", 
            "pn": "1"
        }
        data = await self._http_get(Config.REPLY_DETAIL_URL, params=params, caller="ReplyAction.get_reply_details")

        sub_data = data.get("data", {})
        root_reply = sub_data.get("root") or {}
        replies_list = sub_data.get("replies") or []

        formatted_dialogue = []
        root_username = None

        # 解析并提取根回复
        if root_reply:
            root_username = root_reply.get("member", {}).get("uname")
            formatted_dialogue.append({
                "rpid": root_reply.get("rpid"),
                "mid": root_reply.get("mid"),
                "parent": root_reply.get("parent"),
                "dialog": root_reply.get("dialog"),
                "user": root_username,
                "content": root_reply.get("content", {}).get("message"),
                "reply_to_user": None,
                "is_root": True
            })

        # 解析并提取子回复树列表
        for reply in replies_list:
            if not reply:
                continue
            parent_member = reply.get("parent_reply_member", {})
            reply_to_user = parent_member.get("name") if parent_member else None

            # 默认补全回复目标
            if not reply_to_user and root_username and reply.get("root") != reply.get("rpid"):
                reply_to_user = root_username

            formatted_dialogue.append({
                "rpid": reply.get("rpid"),
                "mid": reply.get("mid"),
                "parent": reply.get("parent"),
                "dialog": reply.get("dialog"),
                "user": reply.get("member", {}).get("uname"),
                "content": reply.get("content", {}).get("message"),
                "reply_to_user": reply_to_user,
                "is_root": False
            })

        return formatted_dialogue
