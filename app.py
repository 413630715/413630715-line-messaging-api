from flask import Flask, abort, request
from dotenv import load_dotenv
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import os

# 載入 .env 中的機密設定，不將憑證寫死在程式碼中。
load_dotenv()

app = Flask(__name__)
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not channel_secret or not access_token:
    raise RuntimeError("請先設定 LINE_CHANNEL_SECRET 與 LINE_CHANNEL_ACCESS_TOKEN")

configuration = Configuration(access_token=access_token)
handler = WebhookHandler(channel_secret)


@app.route("/callback", methods=["POST"])
def callback():
    # 保留原始 body，讓 SDK 驗證 LINE 的數位簽章。
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # reply token 只能使用一次，因此收到事件後立即回覆。
    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        reply = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=event.message.text)],
        )
        messaging_api.reply_message_with_http_info(reply)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
