# 文件路径: notify.py
import os
import requests
import json
import logging
import hmac
import hashlib
import base64
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def send(title, content):
    """
    发送通知消息
    :param title: 消息标题
    :param content: 消息内容
    """
    logging.info(f"尝试发送通知: 标题='{title}', 内容='{content}'")

    # --- Telegram 通知 ---
    tg_bot_token = os.environ.get("TG_BOT_TOKEN")
    tg_user_id = os.environ.get("TG_USER_ID")
    tg_chat_id = os.environ.get("TG_CHAT_ID") # Telegram 群组ID

    if tg_bot_token and (tg_user_id or tg_chat_id):
        # 优先使用 TG_CHAT_ID 发送群组消息，如果不存在则使用 TG_USER_ID 发送给个人
        target_chat_id = tg_chat_id if tg_chat_id else tg_user_id
        
        if not target_chat_id:
            logging.warning("Telegram: 未设置 TG_USER_ID 或 TG_CHAT_ID，跳过通知。")
        else:
            message = f"*{title}*\n\n{content}"
            url = f"https://api.telegram.org/bot{tg_bot_token}/sendMessage"
            payload = {
                "chat_id": target_chat_id,
                "text": message,
                "parse_mode": "Markdown" # 使用 Markdown 格式，标题会加粗
            }
            try:
                response = requests.post(url, json=payload, timeout=10)
                response.raise_for_status() # 检查HTTP错误
                logging.info(f"Telegram 通知已发送到 {target_chat_id}。")
            except requests.exceptions.RequestException as e:
                logging.error(f"发送 Telegram 通知失败: {e}")
    else:
        logging.debug("Telegram: TG_BOT_TOKEN 未设置或 TG_USER_ID/TG_CHAT_ID 未设置，跳过通知。")

    # --- PushPlus 通知 ---
    push_plus_token = os.environ.get("PUSH_PLUS_TOKEN")
    push_plus_user = os.environ.get("PUSH_PLUS_USER") # 可选，用于指定接收者

    if push_plus_token:
        url = "http://www.pushplus.plus/send"
        payload = {
            "token": push_plus_token,
            "title": title,
            "content": content,
            "template": "html" # 或者 "markdown"
        }
        if push_plus_user:
            payload["to"] = push_plus_user
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get("code") == 200:
                logging.info("PushPlus 通知发送成功。")
            else:
                logging.error(f"发送 PushPlus 通知失败: {result.get('msg', '未知错误')}")
        except requests.exceptions.RequestException as e:
            logging.error(f"发送 PushPlus 通知失败: {e}")
    else:
        logging.debug("PushPlus: PUSH_PLUS_TOKEN 未设置，跳过通知。")

    # --- DingTalk (钉钉) 通知 ---
    dd_bot_token = os.environ.get("DD_BOT_TOKEN")
    dd_bot_secret = os.environ.get("DD_BOT_SECRET") # 可选，用于签名

    if dd_bot_token:
        url = f"https://oapi.dingtalk.com/robot/send?access_token={dd_bot_token}"
        headers = {"Content-Type": "application/json;charset=utf-8"}
        
        # 如果有 secret，需要计算签名
        if dd_bot_secret:
            timestamp = str(round(time.time() * 1000))
            string_to_sign = f"{timestamp}\n{dd_bot_secret}"
            hmac_code = hmac.new(dd_bot_secret.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256).digest()
            sign = base64.b64encode(hmac_code).decode('utf-8')
            url += f"&timestamp={timestamp}&sign={sign}"

        payload = {
            "msgtype": "text",
            "text": {
                "content": f"{title}\n\n{content}"
            }
        }
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get("errcode") == 0:
                logging.info("DingTalk 通知发送成功。")
            else:
                logging.error(f"发送 DingTalk 通知失败: {result.get('errmsg', '未知错误')}")
        except requests.exceptions.RequestException as e:
            logging.error(f"发送 DingTalk 通知失败: {e}")
    else:
        logging.debug("DingTalk: DD_BOT_TOKEN 未设置，跳过通知。")

    # --- WxPusher 通知 ---
    wxpusher_app_token = os.environ.get("WXPUSHER_APP_TOKEN")
    # WxPusher 通常需要 uid，这里假设脚本会通过其他方式获取或在内容中包含
    # 如果需要指定 uid，可能需要额外的环境变量 WXPUSHER_UID
    # For simplicity, we'll just send to the app if token is present.

    if wxpusher_app_token:
        url = "http://wxpusher.zjiecode.com/api/send/message"
        payload = {
            "appToken": wxpusher_app_token,
            "content": content,
            "summary": title, # 消息摘要，可选
            "contentType": 1, # 1：文本，2：html，3：markdown
            # "uids": ["UID_HERE"], # 如果需要指定用户，请在此处添加UID列表
            # "url": "https://example.com" # 可选，点击消息跳转的URL
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get("code") == 1000:
                logging.info("WxPusher 通知发送成功。")
            else:
                logging.error(f"发送 WxPusher 通知失败: {result.get('msg', '未知错误')}")
        except requests.exceptions.RequestException as e:
            logging.error(f"发送 WxPusher 通知失败: {e}")
    else:
        logging.debug("WxPusher: WXPUSHER_APP_TOKEN 未设置，跳过通知。")
