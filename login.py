import time
import argparse
import os
import requests
import asyncio
from API import BiliAPI

def set_output(name, value):
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"{name}={value}\n")

async def start_tv_login_flow():
    print("--- 正在申请二维码 ---")
    bili = BiliAPI()
    res1 = await bili.get_tv_qrcode()
    if res1.get("code") != 0:
        print(f"❌ 申请二维码失败: {res1.get('message')}")
        return False

    login_url = res1["data"]["url"]
    auth_code = res1["data"]["auth_code"]
    
    print(f"\n[扫码链接]: {login_url}\n")

    for _ in range(60):
        res2 = await bili.poll_tv_login(auth_code)
        code = res2.get("code")
        
        if code == 0:
            print("\n登录成功！")
            set_output("bili_access_token", res2["data"]["access_token"])
            return True
        elif code == 86039:
            print("... 二维码尚未确认，等待中 ...")
        elif code == 86090:
            print("... 手机已扫码！请在手机上点击【确认登录】...")
        elif code == 86038:
            print("❌ 二维码已失效。")
            break
        else:
            print(f"状态异常 (Code: {code}): {res2.get('message')}")
            break
        await asyncio.sleep(3)
    return False

async def start_web_login_flow():
    print("--- 正在申请二维码链接 ---")
    bili = BiliAPI()
    res1 = await bili.get_web_qrcode()
    if res1.get("code") != 0:
        print(f"❌ 申请二维码失败: {res1.get('message')}")
        return False

    login_url = res1["data"]["url"]
    qrcode_key = res1["data"]["qrcode_key"]

    print(f"\n[扫码链接]: {login_url}\n")    
    session = requests.Session()
    
    for _ in range(60):
        res2 = await bili.poll_web_login(qrcode_key, session)
        code = res2.get("data", {}).get("code")
        
        if code == 0:
            print("\n登录成功！")
            cookies_dict = session.cookies.get_dict()
            set_output("bili_sessdata", cookies_dict.get("SESSDATA", ""))
            set_output("bili_jct", cookies_dict.get("bili_jct", ""))
            return True
        elif code == 86038:
            print("❌ 二维码已失效。")
            break
        elif code == 86090:
            print("... 手机已扫码！请在手机上点击【确认登录】...")
        elif code == 86101:
            print("... 二维码尚未确认，等待中 ...")
        else:
            print(f"状态异常: {res2.get('data', {}).get('message')}")
            break
        await asyncio.sleep(3)
    return False

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['tv', 'web', 'all'], default='all')
    args = parser.parse_args()

    if args.mode in ['tv', 'all']:
        await start_tv_login_flow()
    if args.mode in ['web', 'all']:
        await start_web_login_flow()

if __name__ == "__main__":
    asyncio.run(main())
