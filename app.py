from flask import Flask, request, abort  
from linebot.v3 import WebhookHandler 
from linebot.v3.exceptions import InvalidSignatureError 
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage  
from linebot.v3.webhooks import MessageEvent, TextMessageContent  
from pymongo import MongoClient  
import random 

app = Flask(__name__)  

# 設定Line Messaging API的存取權杖和配置
configuration = Configuration(access_token='ＸＸＸＸＸＸ')# Configuration 用於設置驗證token(API向line發請求的身份驗證)
handler = WebhookHandler('ＸＸＸＸＸＸ')  # 用於設置驗證secret(line向API發起webhook事件的驗證)

# 連接資料庫/建立連結/選擇資料庫
mongo_uri = "mongodb://ＸＸＸＸＸＸ" 
client = MongoClient(mongo_uri)  
db = client.MongoDB  

# 增加畫面豐富度的emoji與增加親近感的開頭語句
emojis = ['🎮', '🕹️', '👾', '💻', '🖥️', '🎲', '🧩', '🎵', '🎶', '🔊']  
greetings = [  
    "知道了主人！現在最新的{category}資訊在這，您快看看～(▰˘◡˘▰)",
    "嘣！馬上變出{category}資訊給你喔～σ`∀´)σ",
    "什麼！有關{category}資訊我找到了這些，主人您滿意嗎？(｡◕∀◕｡)",
    "好，主人您看看這些{category}資訊，很不錯吧！(◕ܫ◕)",
    "沒問題！這些{category}資訊是我拼了老命出去幫你找到的喔 (灬ºωº灬)"
]

# 驗證
@app.route("/callback", methods=['POST'])  
def callback():  
    # 獲取X-Line-Signature請求頭的值
    signature = request.headers['X-Line-Signature']

    # 獲取請求體作為文本
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)  # 紀錄請求體到log

    # 處理Webhook事件驗證
    try:
        handler.handle(body, signature) 
    except InvalidSignatureError: 
        app.logger.info("InvalidSignatureError")  # 紀錄簽名錯誤log
        abort(400)  # abort函數用於立即停止程序，這邊終止請求後並返回400錯誤

    return 'OK'  # 返回OK響應，line那邊收到OK效力等同200

# 訊息處理器，放入收到的訊息事件與文本
@handler.add(MessageEvent, message=TextMessageContent)  
def handle_message(event):  
    msg_text = event.message.text  # 獲取消息文本
    category_labels = {  # 此列表為了依據使用者提交文本，決定回傳的問候語內容要加入哪個訊息
        "/all": "綜合熱門新聞",
        "/game": "手機遊戲情報",
        "/pc": "電腦遊戲情報",
        "/tvgame": "TV掌機情報",
        "/ac": "動漫畫情報",
    }
    
    if msg_text in category_labels:  
        category = msg_text.strip("/")  
        collection_name = f"news_{category}"  # 去除訊息文本開頭的"/'後，加上news_就是我們要撈的資料集名稱
        info_data = db[collection_name].find()  
        greeting = random.choice(greetings).format(category=category_labels[msg_text])  # 隨機選擇一個開頭語句，加入對應的category
        reply_texts = [greeting]  #加入開頭語句到我們的回覆訊息內

        for info in info_data:  
            selected_emoji = random.choice(emojis)  # 隨機選擇一個emoji符號
            reply_texts.append(f"{selected_emoji} {info['title']}: {info['link']}")  # 添加使用者要看的資料到訊息文本（前面放隨機emoji符號）

        reply_text = '\n\n'.join(reply_texts)  # 將回覆文本列表用\n\n合併為一個字符串(讓其空一行優化顯示效果)

        # 尾隨訊息--提示其他指令
        follow_up_msg = "主人除了這些資訊外還有想看看其他的嗎？\n"\
                        "/all  👉 綜合熱門新聞\n"\
                        "/game 👉 手機遊戲情報\n"\
                        "/pc  👉 電腦遊戲情報\n"\
                        "/tvgame 👉 TV掌機情報\n"\
                        "/ac 👉 動漫畫情報"
        
        # 發送上面處理好的訊息
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client) # MessagingApi 是line訊息對應接口方法
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest( # ReplyMessageRequest 專門處理建構回覆訊息的請求
                    reply_token=event.reply_token, 
                    messages=[
                        TextMessage(text=reply_text), # TextMessage 專門處理回覆訊息的文本內容
                        TextMessage(text=follow_up_msg)
                    ]
                )
            )
    else:
        # 如果用戶輸入的不是有效指令，發送提醒
        with ApiClient(configuration) as api_client: # ApiClient 封裝向line平台發送http請求和處理響應的邏輯
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text="請輸入有效的指令，如：/all、/game、/pc、/tvgame 或 /ac。")]))

if __name__ == "__main__":
    app.run()
