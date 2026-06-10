import sqlite3

# مسیر فایل دیتابیس بر اساس توضیحات شما
db_path = "qdrant_data/collection/tweets_collection/storage.sqlite"

# اتصال به دیتابیس
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# دریافت لیست تمام جداول
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("جداول و ستون‌های موجود در دیتابیس Qdrant:")
for table in tables:
    table_name = table[0]
    print(f"\n--- جدول: {table_name} ---")
    
    # دریافت اطلاعات ستون‌های هر جدول
    cursor.execute(f"PRAGMA table_info('{table_name}');")
    columns = cursor.fetchall()
    
    for col in columns:
        col_name = col[1]
        col_type = col[2]
        print(f"  - {col_name} ({col_type})")

conn.close()
