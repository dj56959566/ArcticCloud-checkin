## 使用说明：
创建仓库： 在 GitHub 上创建一个新的仓库。
上传文件： 将上述四个文件按照指定的路径结构上传到你的仓库中。
设置 GitHub Secrets：
进入你的 GitHub 仓库。
点击 "Settings" (设置)。
点击 "Secrets and variables" -> "Actions"。
点击 "New repository secret" (新建仓库 Secret)。
必须设置的 Secret：
ARCTIC_USERNAME: 你的 ArcticCloud 账号
ARCTIC_PASSWORD: 你的 ArcticCloud 密码
通知相关的 Secret (根据你使用的通知方式设置)：
TG_BOT_TOKEN: 你的 Telegram Bot Token
TG_CHAT_ID: 你的 Telegram 群组 chat_id (负数，例如 -123456789)
TG_USER_ID: 你的 Telegram 个人用户 user_id (可选，如果你也想发送给个人)
PUSH_PLUS_TOKEN: PushPlus 的 Token
PUSH_PLUS_USER: PushPlus 的用户标识 (可选)
DD_BOT_TOKEN: 钉钉机器人的 Access Token
DD_BOT_SECRET: 钉钉机器人的 Secret (可选，用于安全签名)
WXPUSHER_APP_TOKEN: WxPusher 的 App Token
其他配置 Secret (可选)：
HEADLESS: true 或 false (默认为 true)
ARCTIC_LOG_LEVEL: INFO, DEBUG, WARNING, ERROR (默认为 INFO)
触发工作流：
工作流会每天中午12点 (UTC时间) 自动运行。
你也可以手动触发：进入仓库的 "Actions" 页面，选择 "ArcticCloud VPS 自动续期" 工作流，点击 "Run workflow" 按钮。
这样，你的 GitHub Actions 就会自动运行脚本，并在续期成功或失败时通过你配置的通知渠道发送消息。
