# -*- coding: utf-8 -*-
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ========== 配置区域 ==========
ARC_USER = os.getenv("ARC_USER", "你的账号")
ARC_PASS = os.getenv("ARC_PASS", "你的密码")

# Telegram 推送
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN"， "你的TG机器人Token")
TG_CHAT_ID = os.getenv("TG_CHAT_ID"， "-100xxxxxx")  # 群聊ID，负数开头

# 截图目录（放当前路径，避免 /ql 权限问题）
SCREENSHOT_DIR = os.path。join(os.getcwd(), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Arctic Cloud 登录地址
ARC_LOGIN_URL = "https://arcticcloud.cn/auth/login"
ARC_DASHBOARD_URL = "https://arcticcloud.cn/user"

# ========== Telegram 发送函数 ==========
def send_tg_message(text, photo_path=None):
    """发送消息到 Telegram 群"""
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT_ID, "text": text}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"发送文字失败: {e}")

    if photo_path and os.path.exists(photo_path):
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
        try:
            with open(photo_path, "rb") as f:
                files = {"photo": f}
                data = {"chat_id": TG_CHAT_ID}
                requests.post(url, data=data, files=files)
        except Exception as e:
            print(f"发送图片失败: {e}")

# ========== 主执行流程 ==========
def main():
    # 配置浏览器
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get(ARC_LOGIN_URL)
        time.sleep(2)

        # 输入账号密码
        driver.find_element(By.NAME, "email").send_keys(ARC_USER)
        driver.find_element(By.NAME, "passwd").send_keys(ARC_PASS)

        # 点击登录
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(5)

        # 进入用户中心
        driver.get(ARC_DASHBOARD_URL)
        time.sleep(3)

        # 截图
        screenshot_path = os.path.join(SCREENSHOT_DIR, f"arc_{int(time.time())}.png")
        driver.save_screenshot(screenshot_path)

        send_tg_message("✅ Arctic Cloud 签到成功", screenshot_path)

    except Exception as e:
        error_msg = f"❌ Arctic Cloud 签到失败: {e}"
        print(error_msg)
        send_tg_message(error_msg)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
