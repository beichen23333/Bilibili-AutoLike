import asyncio
import os
import sys
import time
import uuid
import argparse
from API import BiliAPI
from manager import BlacklistManager


api = BiliAPI(
    access_token=os.getenv("BILI_ACCESS_TOKEN", ""),
    sessdata=os.getenv("BILI_SESSDATA", ""),
    bili_jct=os.getenv("BILI_JCT", "")
)

video_queue = asyncio.Queue()
processed_set = set()
lock = asyncio.Lock()

manager = BlacklistManager()

async def monitor_list():
    loop_count = 0
    while True:
        try:
            loop_count += 1
            if loop_count % 100 == 0:
#                print(f"[DEBUG] monitor_list 运行中，循环次数: {loop_count}, 队列大小: {video_queue.qsize()}, 已处理: {len(processed_set)}")
                pass

#            print(f"[DEBUG] 开始获取最新视频... (循环 #{loop_count})")
            videos = await api.get_latest_videos()
#            print(f"[DEBUG] 获取到 {len(videos) if videos else 0} 个视频")
            
            new_count = 0
            for idx, item in enumerate(videos):
                bvid = item.get("bvid")
#                print(f"[DEBUG] 检查视频 {idx+1}/{len(videos)}: bvid={bvid}")
                
                if bvid and bvid not in processed_set:
#                    print(f"[DEBUG] 发现新视频: {bvid}")
                    processed_set.add(bvid)
                    owner_mid = item.get("owner", {}).get("mid")
#                    print(f"[DEBUG] 将视频加入队列: aid={item.get('aid')}, bvid={bvid}, title={item.get('title', '未知标题')}, owner_mid={owner_mid}")
                    await video_queue.put((item.get("aid"), bvid, item.get("title", "未知标题"), owner_mid))
                    new_count += 1
                elif bvid and bvid in processed_set:
#                    print(f"[DEBUG] 视频 {bvid} 已处理过，跳过")
                    pass
#            print(f"[DEBUG] 本轮新增 {new_count} 个视频到队列")

        except Exception as e:
#            print(f"[ERROR] 监控列表出错: {e}")
            import traceback
            traceback.print_exc()
        
        await asyncio.sleep(0.3)

async def process_video_worker():
    worker_id = id(asyncio.current_task())
#    print(f"[DEBUG] Worker {worker_id} 启动")
    
    while True:
        try:
            aid, bvid, title, owner_mid = await video_queue.get()
            if manager.is_maliciouslisted(owner_mid):
#                print(f"[DEBUG] Worker {worker_id} UID {owner_mid} 在严重黑名单中，执行点踩")
                try:
                    await api.dislike_video(aid, dislike=1)
                except Exception as e:
#                    print(f"[ERROR] Worker {worker_id} 点踩失败: {e}")
                    pass
                continue

#            print(f"[DEBUG] Worker {worker_id} 检查黑名单: owner_mid={owner_mid}")
            if manager.is_blacklisted(owner_mid):
#                print(f"[DEBUG] Worker {worker_id} UID {owner_mid} 在黑名单中，跳过")
                continue

            relation_str = ""
#            print(f"[DEBUG] Worker {worker_id} 获取关系: owner_mid={owner_mid}")
            
            if owner_mid:
#                print(f"[DEBUG] Worker {worker_id} 调用 api.get_relation({owner_mid})")
                relation_res = await api.get_relation(owner_mid)
#                print(f"[DEBUG] Worker {worker_id} get_relation 返回: code={relation_res.get('code')}")
                
                if relation_res.get("code") == 0:
                    be_rel_obj = relation_res.get("data", {}).get("be_relation", {})
                    be_attr = be_rel_obj.get("attribute")
#                    print(f"[DEBUG] Worker {worker_id} be_attr={be_attr}")
                    
                    if be_attr == 2:
                        relation_str = "粉丝"
#                        print(f"[DEBUG] Worker {worker_id} 关系: 粉丝")
                    elif be_attr == 6:
                        relation_str = "互相关注"
#                        print(f"[DEBUG] Worker {worker_id} 关系: 互相关注")

            if relation_str:
#                print(f"[DEBUG] Worker {worker_id} 打印关系信息: {relation_str} | UID: {owner_mid} | 视频: {title} ({bvid})")
                print(f"[{time.strftime('%H:%M:%S')}] 🎯 {relation_str} | UID: {owner_mid} | 视频: {title} ({bvid})")

#            print(f"[DEBUG] Worker {worker_id} 执行点赞: aid={aid}")
            like_res = await api.like_video(aid)
            like_code = like_res.get("code")
#            print(f"[DEBUG] Worker {worker_id} 点赞返回: code={like_code}")

            if like_code == 65011:
#                print(f"[DEBUG] Worker {worker_id} 点赞返回65011，报告被拉黑")
                manager.report_blocked(owner_mid)

            if like_code == 0:
#                print(f"[DEBUG] Worker {worker_id} 点赞成功")
                pass

#            print(f"[DEBUG] Worker {worker_id} 检查收藏夹: api.current_folder_id={api.current_folder_id}")
            if api.current_folder_id:
#                print(f"[DEBUG] Worker {worker_id} 执行收藏: rid={aid}, add_media_ids={api.current_folder_id}")
                fav_res = await api.collect_video(rid=aid, add_media_ids=str(api.current_folder_id))
                code = fav_res.get("code")
#                print(f"[DEBUG] Worker {worker_id} 收藏返回: code={code}")
                
                if code == 0:
                    pass
#                    print(f"[DEBUG] Worker {worker_id} 收藏成功")
                elif code == 412:
                    pass
#                    print(f"[DEBUG] Worker {worker_id} 收藏返回412 (可能重复)")
                elif code in (11201, 11202, 11203):
                    pass
#                    print(f"[DEBUG] Worker {worker_id} 收藏失败 code={code}，尝试更新收藏夹")
                    async with lock:
#                        print(f"[DEBUG] Worker {worker_id} 获取锁成功，更新收藏夹")
                        await api.update_available_folder()
#                        print(f"[DEBUG] Worker {worker_id} 更新后 api.current_folder_id={api.current_folder_id}")
                        if api.current_folder_id:
#                            print(f"[DEBUG] Worker {worker_id} 重试收藏: rid={aid}")
                            retry_res = await api.collect_video(rid=aid, add_media_ids=str(api.current_folder_id))
                            if retry_res.get("code") == 0:
                                pass
#                                print(f"[DEBUG] Worker {worker_id} 重试收藏成功")
                            elif retry_res.get("code") == 412:
                                pass
#                                print(f"[DEBUG] Worker {worker_id} 重试收藏返回412")
                else:
#                    print(f"[DEBUG] Worker {worker_id} 收藏返回其他code: {code}")
                    pass
#            print(f"[DEBUG] Worker {worker_id} 执行分享: bvid={bvid}")
            share_res = await api.share_video(bvid=bvid)
            share_code = share_res.get("code")
#            print(f"[DEBUG] Worker {worker_id} 分享返回: code={share_code}")
            if share_code == 0:
#                print(f"[DEBUG] Worker {worker_id} 分享成功")
                pass
            elif share_code == 412:
#                print(f"[DEBUG] Worker {worker_id} 分享返回412")
                pass
            else:
#                print(f"[DEBUG] Worker {worker_id} 分享返回其他code: {share_code}")
                pass

#            print(f"[DEBUG] Worker {worker_id} 开始播放相关操作: bvid={bvid}")
            try:
#                print(f"[DEBUG] Worker {worker_id} 获取WBI keys")
                img_key, sub_key = await api.get_wbi_keys()
#                print(f"[DEBUG] Worker {worker_id} 获取WBI keys成功")
                
#                print(f"[DEBUG] Worker {worker_id} 获取视频信息: bvid={bvid}")
                info = await api.get_video_info(bvid)
                if info:
#                    print(f"[DEBUG] Worker {worker_id} 获取视频信息成功: aid={info['aid']}, cid={info['cid']}, duration={info['duration']}")
                    real_aid = info["aid"]
                    cid = info["cid"]
                    duration = info["duration"]
                    session_id = uuid.uuid4().hex
#                    print(f"[DEBUG] Worker {worker_id} session_id={session_id}")
                    
                    if relation_str:
                        pass
#                        print(f"[DEBUG] Worker {worker_id} 关系字符串: {relation_str}")

#                    print(f"[DEBUG] Worker {worker_id} 开始观看: real_aid={real_aid}")
                    start_res = await api.start_watch(real_aid)
#                    print(f"[DEBUG] Worker {worker_id} start_watch 返回: {start_res}")
                    
#                    print(f"[DEBUG] Worker {worker_id} 休眠1秒...")
                    await asyncio.sleep(1)
                    
                    mid_point = duration // 2
#                    print(f"[DEBUG] Worker {worker_id} 中间点心跳: mid_point={mid_point}")
                    mid_res = await api.report_heartbeat(bvid, real_aid, cid, mid_point, duration, session_id, img_key, sub_key)
#                    print(f"[DEBUG] Worker {worker_id} mid heartbeat 返回: {mid_res}")
                    
#                    print(f"[DEBUG] Worker {worker_id} 休眠1秒...")
                    await asyncio.sleep(1)
                    
#                    print(f"[DEBUG] Worker {worker_id} 结束点心跳: -1")
                    end_res = await api.report_heartbeat(bvid, real_aid, cid, -1, duration, session_id, img_key, sub_key)
#                    print(f"[DEBUG] Worker {worker_id} end heartbeat 返回: {end_res}")
                    
#                    print(f"[DEBUG] Worker {worker_id} 休眠1秒...")
                    await asyncio.sleep(1)
                    
#                    print(f"[DEBUG] Worker {worker_id} 上报历史: real_aid={real_aid}, cid={cid}, duration={duration}")
                    hist_res = await api.report_history(real_aid, cid, duration)
#                    print(f"[DEBUG] Worker {worker_id} report_history 返回: {hist_res}")
                else:
                    pass
#                    print(f"[ERROR] Worker {worker_id} 获取视频信息失败: info为空")
            except Exception as play_err:
#                print(f"[ERROR] Worker {worker_id} 播放操作异常: {play_err}")
                pass
                import traceback
                traceback.print_exc()

#            print(f"[DEBUG] Worker {worker_id} 视频处理完成: {bvid}")

        except Exception as e:
#            print(f"[ERROR] Worker {worker_id} 处理视频异常: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
#            print(f"[DEBUG] Worker {worker_id} 标记任务完成")
            video_queue.task_done()
#            print(f"[DEBUG] Worker {worker_id} 当前队列大小: {video_queue.qsize()}")

async def run_timer(duration):
#    print(f"[DEBUG] run_timer 启动，持续 {duration} 秒")
    await asyncio.sleep(duration)
#    print(f"[DEBUG] run_timer 时间到，准备退出")
    await api.close()
#    print("[DEBUG] api.close() 完成")
    sys.exit(0)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', type=int, default=18000)
    args = parser.parse_args()
    
    if not await api.init_device_cookies():
        print("[ERROR] init_device_cookies 失败")
        return
    
    if not await api.init_fav_folder():
        print("[ERROR] init_fav_folder 失败")
        return
        
    manager.start_sync()

#    print("[DEBUG] 创建 128 个 worker 任务...")
    workers = [asyncio.create_task(process_video_worker()) for _ in range(128)]
#    print(f"[DEBUG] 已创建 {len(workers)} 个 worker 任务")
    
#    print("[DEBUG] 等待所有任务完成...")
    await asyncio.gather(
        asyncio.create_task(monitor_list()),
        asyncio.create_task(run_timer(args.duration)),
        *workers
    )

if __name__ == "__main__":
    print("[DEBUG] 程序启动")
    try:
        asyncio.run(main())
        print("[DEBUG] asyncio.run(main()) 正常结束")
    except KeyboardInterrupt:
        print("\n[DEBUG] 收到 KeyboardInterrupt，正在退出...")
    except Exception as e:
        print(f"[ERROR] 程序异常: {e}")
        import traceback
        traceback.print_exc()