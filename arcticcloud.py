# -*- coding: utf-8 -*-
import os
import sys
import time
import logging
import traceback
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# 环境变量配置
USERNAME = os.environ.get("ARCTIC_USERNAME")
PASSWORD = os.environ.get("ARCTIC_PASSWORD")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

WAIT_TIMEOUT = 60
HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"
ENABLE_SCREENSHOT = False

# 页面地址
LOGIN_URL = "https://vps.polarbear.nyc.mn/index/login/?referer="
CONTROL_INDEX_URL = "https://vps.polarbear.nyc.mn/control/index/"

# 截图目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# 设置日志，支持中文和utf-8
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logging.getLogger().handlers[0].setFormatter(logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s"))

def send_telegram(title, content):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        logging.warning("Telegram 推送配置缺失，跳过发送。")
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TG_CHAT_ID,
        "text": f"{title}\n{content}",
        "parse_mode": "Markdown"
    }
    try:
        resp = requests.post(url, data=data, timeout=15)
        if resp.status_code == 200:
            logging.info("Telegram 推送成功")
        else:
            logging.error(f"Telegram 推送失败，状态码 {resp.status_code}，响应：{resp.text}")
    except Exception as e:
        logging.error(f"Telegram 推送异常: {e}")

def take_screenshot(driver, filename):
    if not ENABLE_SCREENSHOT:
        return
    path = os.path.join(SCREENSHOT_DIR, filename)
    driver.save_screenshot(path)
    logging.info(f"截图已保存到 {path}")

def setup_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
    if HEADLESS:
        options.add_argument("--headless=new")  # 推荐使用新版headless模式
        options.add_argument("--disable-blink-features=AutomationControlled")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    if HEADLESS:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_window_size(1920, 1080)

    return driver

def login_with_credentials(driver):
    logging.info("开始登录...")
    if not USERNAME or not PASSWORD:
        raise ValueError("缺少 ARCTIC_USERNAME 或 ARCTIC_PASSWORD 环境变量")

    driver.get(LOGIN_URL)
    email_input = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.NAME, "swapname"))
    )
    email_input.send_keys(USERNAME)

    password_input = driver.find_element(By.NAME, "swappass")
    password_input.send_keys(PASSWORD)

    login_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., '登录')]"))
    )
    login_button.click()

    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.url_contains("index/index")
    )
    logging.info("登录成功")

def navigate_to_control_index(driver):
    logging.info("访问控制台首页...")
    driver.get(CONTROL_INDEX_URL)
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.url_contains("control/index")
    )
    logging.info("进入控制台首页")

def find_and_renew_instances(driver):
    logging.info("查找 VPS 实例列表...")
    manage_buttons = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//a[contains(@class,'btn btn-primary') and contains(@href,'/control/detail/')]")
        )
    )
    if not manage_buttons:
        logging.warning("没有找到任何实例")
        return

    for idx, btn in enumerate(manage_buttons, 1):
        href = btn.get_attribute("href")
        instance_id = href.split("/")[-2]
        instance_name = btn.text.strip() or "未命名实例"
        logging.info(f"处理实例 {idx}/{len(manage_buttons)}: 名称={instance_name} ID={instance_id}")

        driver.get(f"https://vps.polarbear.nyc.mn/control/detail/{instance_id}/")
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.url_contains(f"/control/detail/{instance_id}/")
        )

        try:
            renew_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-target='#addcontactmodal']"))
            )
            renew_button.click()
            logging.info(f"点击续期按钮，实例：{instance_name}")

            submit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input.btn.m-b-xs.w-xs.btn-success.install-complete"))
            )
            submit_button.click()
            logging.info(f"点击确认续期按钮，实例：{instance_name}")

            try:
                success_alert = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'alert-success')]"))
                )
                logging.info(f"续期成功，消息: {success_alert.text}")
            except TimeoutException:
                logging.warning("未检测到续期成功提示，可能续期成功但页面无反馈")
                take_screenshot(driver, f"success_alert_missing_{instance_id}.png")

            # 读取续期到期时间
            list_group_items = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_all_elements_located((By.XPATH, "//li[@class='list-group-item']"))
            )
            expiration_text = "未找到到期时间信息"
            if len(list_group_items) >= 5:
                full_text = list_group_items[4].text.strip()
                if "到期时间" in full_text:
                    start = full_text.find("到期时间")
                    end = full_text.find("状态") if "状态" in full_text else len(full_text)
                    expiration_text = full_text[start:end].strip()
            logging.info(f"实例 {instance_name} 续期成功，{expiration_text}")

            send_telegram("ArcticCloud续期成功", f"实例 {instance_name} 续期成功，{expiration_text}")

        except Exception as e:
            logging.error(f"续期实例 {instance_name} 出错: {e}", exc_info=True)
            take_screenshot(driver, f"renew_error_{instance_id}.png")

def main():
    driver = None
    try:
        logging.info("启动自动续期...")
        driver = setup_driver()
        login_with_credentials(driver)
        navigate_to_control_index(driver)
        find_and_renew_instances(driver)
    except Exception:
        logging.error("主程序异常退出", exc_info=True)
    finally:
        if driver:
            logging.info("关闭浏览器")
            driver.quit()
        logging.info("脚本执行结束")

if __name__ == "__main__":
    main()
