import json
import redis
from matcher import PersistentMinHashMatcher

def load_initial_data():
    matcher = PersistentMinHashMatcher(threshold=0.75)
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    # اضافه شده: پاک کردن کل داده‌های قبلی در Redis برای جلوگیری از خطای کلید تکراری
    print("در حال پاک‌سازی دیتابیس Redis...")
    redis_client.flushdb() 
    
    with open('content.json', 'r', encoding='utf-8') as f:
        tweets_data = json.load(f)
        
    print("در حال ایندکس کردن داده‌ها در Redis...")
    for idx, tweet in enumerate(tweets_data[:1000]):
        tweet_content = tweet.get('content', '')
        if tweet_content:
            doc_id = f"tweet_{idx}"
            
            # ایندکس کردن در LSH
            matcher.insert(doc_id, tweet_content)
            
            # ذخیره متن اصلی در ردیس
            redis_client.set(f"tweet_text:{doc_id}", tweet_content)
            
    print("ایندکس ۱۰۰۰ توییت و ذخیره متن آن‌ها با موفقیت تمام شد.")

if __name__ == "__main__":
    load_initial_data()
