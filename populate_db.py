import json
import time
import uuid
from datetime import datetime
from core.preprocess import clean_text
from core.embedder import BGEEmbedder
from core.vector_db import QdrantManager
from core.exact_match import MinHashMatcher

def parse_date_to_timestamp(date_str):
    """
    تبدیل رشته تاریخ به عدد Timestamp
    """
    if not date_str:
        return time.time()
    try:
        # برای اطمینان از پشتیبانی fromisoformat، فاصله را با T جایگزین می‌کنیم
        dt = datetime.fromisoformat(date_str.replace(' ', 'T'))
        return dt.timestamp()
    except Exception as e:
        print(f"Warning: Could not parse date {date_str}, using current time. Error: {e}")
        return time.time()

def main():
    print("Initializing modules...")
    embedder = BGEEmbedder()
    db = QdrantManager()
    minhash_matcher = MinHashMatcher()

    print("Loading data from content.json...")
    try:
        with open('content.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: File 'content.json' not found. Please make sure it's in the same directory.")
        return

    print(f"Found {len(data)} records. Starting to process...")

    inserted_count = 0
    for item in data:
        content = item.get('content')
        created_at_str = item.get('created_at')
        
        # اگر رکورد محتوای متنی نداشت از آن عبور کن
        if not content:
            continue

        # ۱. تولید یک ID یکتا برای این رکورد به شکل UUID
        # دیتابیس Qdrant شناسه‌های UUID را به عنوان استرینگ می‌پذیرد
        item_id = str(uuid.uuid4())

        # ۲. تبدیل زمان متنی به عدد timestamp
        timestamp = parse_date_to_timestamp(created_at_str)

        # ۳. تمیزسازی متن (حذف کاراکترهای اضافه و استانداردسازی)
        cleaned_text = clean_text(content)
        
        # نادیده گرفتن متن‌های خیلی کوتاه (مثل کلمه hmg در خط اول دیتای شما یا test)
        # طبق تنظیمات پروژه شما، متون کوتاه ارزش برداری سازی ندارند
        if len(cleaned_text) < 10: 
            continue

        # ۴. تبدیل به بردار با مدل BGE-M3 (تولید Dense و Sparse)
        encoded_data = embedder.encode(cleaned_text)
        dense_vec = encoded_data['dense']
        sparse_vec = encoded_data['sparse']

        # ۵. ذخیره در Qdrant
        db.insert_tweet(item_id, dense_vec, sparse_vec, timestamp)

        # ۶. ذخیره در MinHash برای تشخیص کپی‌های دقیق در آینده
        minhash_matcher.insert(item_id, cleaned_text)

        inserted_count += 1
        if inserted_count % 100 == 0:
            print(f"{inserted_count} records inserted...")

    print(f"Successfully populated Qdrant and Minhash with {inserted_count} records!")

if __name__ == "__main__":
    main()
