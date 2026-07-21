import os

class Config:
    # Bilibili 官方应用凭证 (常规 App 与 TV 端)
    APP_KEY = "1d8b6e7d4232f995"
    APP_SEC = "560c52ccd288fed045859ed18bffd973"

    TV_APP_KEY = "783bbb7264451d82"
    TV_APP_SEC = "2653583c8873dea268ab9386918b1d65"

    # HTTP 客户端连接池控制
    MAX_KEEPALIVE_CONNECTIONS = 300
    MAX_CONNECTIONS = 1000
    TIMEOUT = 3.0

    # 默认浏览器与应用请求头
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    APP_USER_AGENT = "Mozilla/5.0 BiliApp/7.80.0"

    # 大模型 API 配置 (DeepSeek)
    DS_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DS_URL = "https://api.deepseek.com/v1/chat/completions"
    MY_NAME = "挽樱_Official"

    # WBI 签名默认降级混淆密钥
    WBI_FALLBACK_KEY = "1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q"

    # WBI 混淆查表数组
    WBI_ENC_TAB = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
        33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40, 61,
        26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36,
        20, 34, 44, 52
    ]

    # API 地址

    # 基础
    SPI_URL = "https://api.bilibili.com/x/frontend/finger/spi"
    HOME_URL = "https://www.bilibili.com/"
    NAV_URL = "https://api.bilibili.com/x/web-interface/nav"

    # 登录
    TV_QRCODE_URL = "https://passport.snm0516.aisee.tv/x/passport-tv-login/qrcode/auth_code"
    TV_POLL_URL = "https://passport.snm0516.aisee.tv/x/passport-tv-login/qrcode/poll"
    WEB_QRCODE_URL = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
    WEB_POLL_URL = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"

    # TV登录头
    TV_USER_AGENT = "Mozilla/5.0 BiliTV/1.el9 (Linux; U; Android 9; zh_CN; MI BOX)..."

    # 历史记录
    HISTORY_CLICK_URL = "https://api.bilibili.com/x/click-interface/click/web/h5"
    HISTORY_HEARTBEAT_URL = "https://api.bilibili.com/x/click-interface/web/heartbeat"
    HISTORY_REPORT_URL = "https://api.bilibili.com/x/v2/history/report"

    # 获取新视频
    VIDEO_NEWLIST_URL = "https://api.bilibili.com/x/web-interface/newlist"
    VIDEO_RELATION_URL = "https://api.bilibili.com/x/web-interface/relation"
    VIDEO_VIEW_URL = "https://api.bilibili.com/x/web-interface/view"

    # 发表/回复评论
    REPLY_ADD_URL = "https://api.bilibili.com/x/v2/reply/add"

    # 点赞评论
    REPLY_ACTION_URL = "https://api.bilibili.com/x/v2/reply/action"

    # 获取未读评论/回复消息通知列表
    REPLY_MSG_FEED_URL = "https://api.bilibili.com/x/msgfeed/reply"

    # 获取特定根评论下子评论对话树明细
    REPLY_DETAIL_URL = "https://api.bilibili.com/x/v2/reply/reply"

    # 点踩
    APP_DISLIKE_URL = "https://app.biliapi.net/x/v2/view/dislike"

    # 点赞
    APP_LIKE_URL = "https://app.bilibili.com/x/v2/view/like"
    
    FAV_FOLDER_LIST_URL = "https://api.bilibili.com/x/v3/fav/folder/created/list-all"

    FAV_FOLDER_ADD_URL = "https://api.bilibili.com/x/v3/fav/folder/add"

    NAV_URL = "https://api.bilibili.com/x/web-interface/nav"

    FAV_RESOURCE_DEAL_URL = "https://api.bilibili.com/medialist/gateway/coll/resource/deal"

    SHARE_ADD_URL = "https://api.bilibili.com/x/web-interface/share/add"

    DANMAKU_POST_URL = "https://api.bilibili.com/x/v2/dm/post"

    SPACE_SEARCH_URL = "https://api.bilibili.com/x/space/wbi/arc/search"

