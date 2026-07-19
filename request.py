import asyncio
import os
import sys
import time
import uuid
import argparse
from API import BiliAPI
from crypto_utils import BlacklistDecryptor

api = BiliAPI(
    access_token=os.getenv("BILI_ACCESS_TOKEN", ""),
    sessdata=os.getenv("BILI_SESSDATA", ""),
    bili_jct=os.getenv("BILI_JCT", "")
)

video_queue = asyncio.Queue()
processed_set = set()
lock = asyncio.Lock()

decryptor = BlacklistDecryptor()

async def monitor_list():
    while True:
        try:
            videos = await api.get_latest_videos()
            new_count = 0
            for item in videos:
                bvid = item.get("bvid")
                if bvid and bvid not in processed_set:
                    processed_set.add(bvid)
                    owner_mid = item.get("owner", {}).get("mid")
                    await video_queue.put((item.get("aid"), bvid, item.get("title", "未知标题"), owner_mid))
                    new_count += 1
        except Exception as e:
            print(f"监控列表出错: {e}")
            pass
        
        await asyncio.sleep(0.3)

async def process_video_worker():
    while True:
        aid, bvid, title, owner_mid = await video_queue.get()
        
        try:
            if decryptor.is_severe_blacklisted(owner_mid):
                try:
                    await api.dislike_video(aid, dislike=1)
                except:
                    pass
                continue

            if decryptor.is_blacklisted(owner_mid):
                continue

            relation_str = ""
            
            if owner_mid:
                relation_res = await api.get_relation(owner_mid)
                if relation_res.get("code") == 0:
                    be_rel_obj = relation_res.get("data", {}).get("be_relation", {})
                    be_attr = be_rel_obj.get("attribute")
                    
                    if be_attr == 2:
                        relation_str = "粉丝"
                    elif be_attr == 6:
                        relation_str = "互相关注"

            if relation_str:
                print(f"[{time.strftime('%H:%M:%S')}] 🎯 {relation_str} | UID: {owner_mid} | 视频: {title} ({bvid})")

            like_res = await api.like_video(aid)
            like_code = like_res.get("code")

            if like_code == 65011:
                try:
                    decryptor.report_blocked_me(owner_mid)
                except:
                    pass
                continue

            if like_code == 0:
                pass
            elif like_code != -999:
                pass

            if api.current_folder_id:
                fav_res = await api.collect_video(rid=aid, add_media_ids=str(api.current_folder_id))
                code = fav_res.get("code")
                
                if code == 0:
                    pass
                elif code == 412:
                    pass
                elif code in (11201, 11202, 11203):
                    async with lock:
                        await api.update_available_folder()
                        if api.current_folder_id:
                            retry_res = await api.collect_video(rid=aid, add_media_ids=str(api.current_folder_id))
                            if retry_res.get("code") == 0:
                                pass
                            elif retry_res.get("code") == 412:
                                pass
                else:
                    pass

            share_res = await api.share_video(bvid=bvid)
            share_code = share_res.get("code")
            if share_code == 0:
                pass
            elif share_code == 412:
                pass
            else:
                pass

            try:
                img_key, sub_key = await api.get_wbi_keys()
                info = await api.get_video_info(bvid)
                if info:
                    real_aid = info["aid"]
                    cid = info["cid"]
                    duration = info["duration"]
                    session_id = uuid.uuid4().hex
                    
                    if relation_str:
                        pass

                    start_res = await api.start_watch(real_aid)
                    await asyncio.sleep(1)
                    
                    mid_point = duration // 2
                    mid_res = await api.report_heartbeat(bvid, real_aid, cid, mid_point, duration, session_id, img_key, sub_key)
                    await asyncio.sleep(1)
                    
                    end_res = await api.report_heartbeat(bvid, real_aid, cid, -1, duration, session_id, img_key, sub_key)
                    await asyncio.sleep(1)
                    
                    hist_res = await api.report_history(real_aid, cid, duration)
                else:
                    pass
            except Exception as play_err:
                pass

        except Exception as e:
            pass
        
        finally:
            video_queue.task_done()

async def run_timer(duration):
    await asyncio.sleep(duration)
    await api.close()
    sys.exit(0)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', type=int, default=18000)
    args = parser.parse_args()
    
    if not await api.init_device_cookies():
        return
    
    if not await api.init_fav_folder():
        return
        
    decryptor.start_sync()
        
    workers = [asyncio.create_task(process_video_worker()) for _ in range(128)]
    
    await asyncio.gather(
        asyncio.create_task(monitor_list()),
        asyncio.create_task(run_timer(args.duration)),
        *workers
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n正在退出...")
