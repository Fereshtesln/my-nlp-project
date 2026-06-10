import time
import redis
from core.preprocess import clean_text
from matcher import PersistentMinHashMatcher 
from core.embedder import BGEEmbedder
from core.vector_db import QdrantManager

# --- تنظیمات اولیه ---
MIN_TWEET_LENGTH = 60
SIMILARITY_THRESHOLD = 0.60

# --- راه‌اندازی ماژول‌ها ---
print("Initializing modules...")
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
minhash_matcher = PersistentMinHashMatcher(threshold=0.80) 
embedder = BGEEmbedder()
db = QdrantManager()
print("Modules initialized successfully!\n")

def check_tweet_originality(tweet_id, text, timestamp):
    """
    بررسی اصالت توییت و ثبت آن در سیستم
    """
    # ۱. پیش‌پردازش
    cleaned_text = clean_text(text)
    if len(cleaned_text) < MIN_TWEET_LENGTH:
        return {"id": tweet_id, "status": "ignored", "reason": "Too short after cleaning."}

    # ۲. بررسی کپی عینی (MinHash)
    exact_matches = minhash_matcher.query(cleaned_text) 
    if exact_matches: # اگر لیستی از شناسه‌های مشابه برگشت داده شد
        matched_texts = []
        for match_id in exact_matches:
            # خواندن متن توییت اصلی از Redis
            orig_text = redis_client.get(f"tweet_text:{match_id}")
            matched_texts.append(f"  - شناسه {match_id}: {orig_text}")
            
        reason_msg = f"Exact/Near-exact match found (MinHash).\nمتن‌های مشابه:\n" + "\n".join(matched_texts)
        return {"id": tweet_id, "status": "copy", "reason": reason_msg}

    # ۳. تولید بردارهای معنایی و کلمات کلیدی
    encoded_data = embedder.encode(cleaned_text)
    dense_vec = encoded_data['dense']
    sparse_vec = encoded_data['sparse']
    
    print("--- Before search_similar ---")
    print(f"Type of dense_vec: {type(dense_vec)}")
    print(f"Content of dense_vec: {dense_vec[:5]}...")
    print(f"Type of sparse_vec: {type(sparse_vec)}")
    print(f"Content of sparse_vec: {sparse_vec}")
    print("---------------------------")

    # ۴. جستجوی توییت‌های مشابه در Qdrant
    similar_tweets = db.search_similar(dense_vec, sparse_vec, limit=3)
    print(f"\n--- بررسی امتیاز شباهت برای توییت جدید ---")
    if similar_tweets:
        for result in similar_tweets:
            print(f"توییت مشابه پیدا شد -> ID: {result.id} | امتیاز شباهت: {result.score:.4f}")
    else:
        print("هیچ توییت مشابهی در دیتابیس یافت نشد.")
    print("------------------------------------------\n")
        
    is_copy = False
    original_tweet_id = None
    matched_score = 0.0

    for match in similar_tweets:
        if match.score >= SIMILARITY_THRESHOLD:
            if match.payload["timestamp"] < timestamp:
                is_copy = True
                original_tweet_id = match.id
                matched_score = match.score
                break

    if is_copy:
        # اگر می‌خواهید متن توییت مشابه در Qdrant را هم نشان دهید:
        qdrant_orig_text = redis_client.get(f"tweet_text:{original_tweet_id}")
        return {
            "id": tweet_id, 
            "status": "copy", 
            "reason": f"Semantic copy of tweet {original_tweet_id} (Score: {matched_score:.2f})\nمتن مشابه: {qdrant_orig_text}"
        }

    # ۵. ثبت توییت در سیستم برای مقایسه‌های آینده
    minhash_matcher.insert(tweet_id, cleaned_text)
    # ذخیره متن توییت جدید در Redis برای نمایش در جستجوهای بعدی
    redis_client.set(f"tweet_text:{tweet_id}", text) 
    
    db.insert_tweet(tweet_id, dense_vec, sparse_vec, timestamp,text)

    # ۶. نتیجه‌گیری نهایی
    return {"id": tweet_id, "status": "original", "reason": "No prior matching tweet found."}

# ==========================================
# تست سیستم
# ==========================================
if __name__ == "__main__":
    tweets = [
        #{"id": 10004, "text":"هوش مصنوعی در سال‌های آینده بازار کار برنامه‌نویسی را به شدت متحول خواهد کرد", "timestamp": 1780790400},
        #{"id": 10005, "text":"هوش مصنوعی در سالهای اینده بازار کار برنامه نویسی را بشدت متحول میکند", "timestamp": 1780890400},
        #{"id": 10008, "text":"پیشرفت‌های اخیر در هوش مصنوعی و مدل‌های زبانی، به زودی روال روزمره برنامه‌نویسان و فرآیند کدنویسی را به طور بنیادین دگرگون خواهد کرد", "timestamp": 1780790492},
        {"id": 10010, "text":"چطورین احوال سلام به همگی", "timestamp": 1780790400}
    ]

    print("--- Starting Tweet Originality Check Pipeline ---\n")
    for tw in tweets:
        result = check_tweet_originality(tw["id"], tw["text"], tw["timestamp"])
        print(f"Tweet {tw['id']} | Status: {result['status']} | Reason:\n{result['reason']}\n")
    if hasattr(db, 'client'):
        db.client.close()
