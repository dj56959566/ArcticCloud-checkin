# -*- coding:utf-8 -*-
import os
import time
import logging
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# ============ 配置开关 ============
WAIT_TIMEOUT = 60
ENABLE_SCREENSHOT = False
HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"
LOG_LEVEL = os.environ.get("ARCTIC_LOG_LEVEL", "INFO").upper()
# ===============================

# 环境变量
USERNAME = os.environ.get("ARCTIC_USERNAME")
PASSWORD = os.environ.get("ARCTIC_PASSWORD")

# Telegram配置
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

# 页面地址
LOGIN_URL = "https://vps.polarbear.nyc.mn/index/login/?referer="
CONTROL_INDEX_URL = "https://vps.polarbear.nyc.mn/control/index/"

# 截图目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# 日志配置
numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)
logging.basicConfig(
    level=numeric_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def send_telegram(text: str):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        logging.warning("未配置 Telegram 推送参数，跳过推送")
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code == 200:
            logging.info("Telegram 推送成功")
        else:
            logging.error(f"Telegram 推送失败，状态码 {resp.status_code}，响应：{resp.text}")
    except Exception as e:
        logging.error(f"Telegram 推送异常：{e}")

def take_screenshot(driver, filename="error.png"):
    if not ENABLE_SCREENSHOT:
        return
    path = os.path.join(SCREENSHOT_DIR, filename)
    driver.save_screenshot(path)
    logging.debug(f"📸 已保存截图至: {path}")

def setup_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
    if HEADLESS:
        options.add_argument("--headless=new")  # 最新chrome headless模式
        options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    if HEADLESS:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_window_size(1920, 1080)
    return driver

def login_with_credentials(driver):
    logging.info("开始登录...")
    if not USERNAME or not PASSWORD:
        raise ValueError("缺少 ARCTIC_USERNAME 或 ARCTIC_PASSWORD 环境变量")

    driver.get(LOGIN_URL)
    email_input = WebDriverWait(driver, WAIT_TIMEOUT).until(EC.presence_of_element_located((By.NAME, "swapname")))
    email_input.send_keys(USERNAME)
    password_input = driver.find_element(By.NAME, "swappass")
    password_input.send_keys(PASSWORD)
    login_btn = WebDriverWait(driver, WAIT_TIMEOUT).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '登录')]")))
    login_btn.click()

    WebDriverWait(driver, WAIT_TIMEOUT).until(EC.url_contains("index/index"))
    logging.info("登录成功")

def navigate_to_control_index(driver):
    logging.info("访问控制台首页...")
    driver.get(CONTROL_INDEX_URL)
    WebDriverWait(driver, WAIT_TIMEOUT).until(EC.url_contains("control/index"))
    logging.info("进入控制台首页")

def find_and_navigate_to_instance_consoles(driver):
    logging.info("查找实例...")
    manage_buttons = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//a[contains(@class, 'btn btn-primary') and contains(@href, '/control/detail/')]")
        )
    )
    instance_ids = [btn.get_attribute('href').split('/')[-2] for btn in manage_buttons]
    if not instance_ids:
        raise ValueError("未找到实例")

    for idx, instance_id in enumerate(instance_ids, 1):
        logging.info(f"处理实例 {idx}/{len(instance_ids)}: {instance_id}")
        driver.get(f"https://vps.polarbear.nyc.mn/control/detail/{instance_id}/")
        WebDriverWait(driver, WAIT_TIMEOUT).until(EC.url_contains(f"/control/detail/{instance_id}/"))
        renew_vps_instance(driver, instance_id)

def renew_vps_instance(driver, instance_id):
    logging.info(f"续期实例 {instance_id}...")
    try:
        renew_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-target='#addcontactmodal']"))
        )
        renew_button.click()
        submit_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input.btn.m-b-xs.w-xs.btn-success.install-complete"))
        )
        submit_btn.click()
        success_alert = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='alert alert-success']"))
        )
        logging.info(f"续期成功: {success_alert.text}")

        # 获取到期时间
        list_items = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_all_elements_located((By.XPATH, "//li[@class='list-group-item']"))
        )
        expiration_info = "未找到到期时间"
        if len(list_items) >= 5:
            txt = list_items[4].text
            if "到期时间" in txt:
                start = txt.find("到期时间")
                end = txt.find("状态") if "状态" in txt else len(txt)
                expiration_info = txt[start:end].strip()
        msg = f"实例 {instance_id} 续期成功，{expiration_info}"
        logging.info(msg)
        send_telegram(msg)
    except Exception as e:
        logging.error(f"续期失败: {e}", exc_info=True)
        take_screenshot(driver, f"renew_error_{instance_id}.png")
        send_telegram(f"实例 {instance_id} 续期失败：{e}")

def main():
    driver = None
    try:
        logging.info("启动自动续期...")
        driver = setup_driver()
        login_with_credentials(driver)
        navigate_to_control_index(driver)
        find_and_navigate_to_instance_consoles(driver)
        logging.info("所有实例续期完成")
    except Exception:
        logging.error("主程序异常退出", exc_info=True)
        send_telegram("⚠️ ArcticCloud 自动续期脚本执行失败，请检查日志")
    finally:
        if driver:
            driver.quit()
        logging.info("脚本执行结束")

if __name__ == "__main__":
    main()
