import asyncio
import os
import argparse
from API import BiliAPI

api = BiliAPI(
    access_token=os.getenv("BILI_ACCESS_TOKEN", ""),
    sessdata=os.getenv("BILI_SESSDATA", ""),
    bili_jct=os.getenv("BILI_JCT", ""),
    DeepSeek=os.getenv("DEEPSEEK_API_KEY", "")
)

async def process_single_msg(api, msg):
    if msg['oid'] and msg['root_id']:
        dialogue = await api.get_reply_details(msg['oid'], msg['root_id'])
        if dialogue:
            parent_id = msg['root_id']
            for turn in dialogue:
                if turn['is_root']:
                    print(f"【楼主】[{turn['user']}]: {turn['content']}")
                elif turn['reply_to_user']:
                    print(f"  └─ 用户 [{turn['user']}] 回复 [{turn['reply_to_user']}]: {turn['content']}")
                else:
                    print(f"  └─ 用户 [{turn['user']}]: {turn['content']}")
                
                if turn['user'] == msg['user']:
                    parent_id = turn['rpid']

            ai_reply = await api.get_ai_reply(dialogue, target_user=msg['user'])
            print(f"\n{ai_reply}")
            print(msg['type_code'])
            reply_res = await api.add_reply(oid=msg['oid'], message=ai_reply, r_type=msg['type_code'], root_id=msg['root_id'], parent_id=parent_id)
            if reply_res and reply_res.get("code") == 0:
                rpid = reply_res.get("data", {}).get("rpid")
                if rpid:
                    await api.action_reply(oid=msg['oid'], rpid=rpid, action=1)
            
        print("-" * 30)

async def message_loop():
    while True:
        try:
            unread = await api.get_unread_replies()
            
            if unread:
                for msg in unread:
                    await process_single_msg(api, msg)

        except Exception as e:
            import traceback
            traceback.print_exc()

            # 不清楚什么原因导致的部分无法获取。
        await asyncio.sleep(30)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', type=int, default=18000, help="运行持续时间（秒）")
    args = parser.parse_args()
    try:
        await asyncio.wait_for(message_loop(), timeout=args.duration)
    except asyncio.TimeoutError:
        print(f"\n已达到设定的运行时间 ({args.duration} 秒)，正在准备退出...")
    finally:
        await api.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n正在退出...")
