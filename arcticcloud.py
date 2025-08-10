# -*- coding: utf-8 -*-
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# 读取环境变量
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")
AC_USERNAME = os.getenv("AC_USERNAME", "")
AC_PASSWORD = os.getenv("AC_PASSWORD", "")
AC_URL = os.getenv("AC_URL", "https://arcticcloud.example.com/login")

def send_telegram_message(message):
    """推送到 Telegram 群"""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("❌ 未设置 Telegram 推送信息")
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": TG_CHAT_ID,
            "text": message
        })
        print("✅ 已发送到 Telegram")
    except Exception as e:
        print("❌ Telegram 推送失败：", e)

def arcticcloud_checkin():
    """ArcticCloud 自动签到"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(AC_URL)
    time.sleep(2)

    try:
        driver.find_element("name", "username").send_keys(AC_USERNAME)
        driver.find_element("name", "password").send_keys(AC_PASSWORD)
        driver.find_element("xpath", "//button[@type='submit']").click()
        time.sleep(3)

        # 点击签到按钮（这里根据实际页面调整选择器）
        driver.find_element("xpath", "//button[contains(text(),'签到')]").click()
        time.sleep(2)

        message = f"🌟 ArcticCloud 签到成功！账号：{AC_USERNAME}"
        print(message)
        send_telegram_message(message)

    except Exception as e:
        message = f"❌ ArcticCloud 签到失败：{e}"
        print(message)
        send_telegram_message(message)

    finally:
        driver.quit()

if __name__ == "__main__":
    arcticcloud_checkin()
