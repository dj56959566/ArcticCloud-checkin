# ArcticCloud 自动续期脚本(现可以多个实例推送)

支持 GitHub Actions 自动续期 ArcticCloud VPS，并推送续期状态到 Telegram bot/群。现更新为北京时间每天早上8点

## 使用方法

1. Fork 本仓库。
2. 在 Settings -> Secrets 和 variables -> Actions 添加以下 Secret：
   - ARCTIC_USERNAME ：你的 ArcticCloud 账号
   - 
   - ARCTIC_PASSWORD ：你的密码
   - 
   - TG_BOT_TOKEN ：你的 Telegram 机器人 Token
   - 
   - TG_CHAT_ID ：你的 Telegram 群聊 ID （格式如 -1001234567890）
   - 
3. 提交后 GitHub Actions 会每天自动运行，也支持手动触发。

---

脚本基于 Selenium + webdriver-manager，无需手动安装 ChromeDriver。
