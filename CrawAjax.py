from pymongo import MongoClient
import urllib.request as req
import json
import schedule
import time

url_base = "https://www.gamer.com.tw/ajax/gnn.php?area=featurednews&tab="
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}

class GameNewsScraper:
    def fetch_news(self, categories):
        url = url_base + categories
        request = req.Request(url, headers=headers)

        with req.urlopen(request) as response:
            data = response.read().decode("utf-8")
        data = json.loads(data)

        extracted_info = []
        for item in data['data']['list']:
            extracted_info.append({'title': item['title'], 'link': "https://gnn.gamer.com.tw/detail.php?sn=" + str(item['sn'])})

        return extracted_info

class MongoDBManager:
    def __init__(self, uri, db_name):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def insert_data(self, data, collection_name):
        collection = self.db[collection_name]
        collection.delete_many({})  # 注意：這會刪除集合中的所有資料
        if data:
            collection.insert_many(data)  

    def close(self):
        self.client.close()

def run_scraper():
    scraper = GameNewsScraper()
    mongo_manager = MongoDBManager("mongodb://XXXXXX", "MongoDB")

    categories = {
        'all': "all",
        'game': "mobile",
        'pc': "pc",
        'tvgame': "tv",
        'ac': "acn"
    }

    try:
        for key, category in categories.items():
            news_data = scraper.fetch_news(category)
            mongo_manager.insert_data(news_data, f"news_{key}")
    finally:
        mongo_manager.close()
    print("Scraper run completed")

def run_scheduler():
    # 定義任務執行的時間，例如每天的9:00
    schedule.every().day.at("09:00").do(run_scraper)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run_scheduler()
