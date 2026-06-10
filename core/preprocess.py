# core/preprocess.py
import re

def clean_text(text: str) -> str:
    if not text:
        return ""
    
    # تبدیل ی و ک عربی به فارسی
    text = text.replace('ي', 'ی').replace('ك', 'ک')
    
    # حذف لینک‌ها
    text = re.sub(r'http[s]?://\S+', '', text)
    
    # حذف منشن‌ها (@username)
    text = re.sub(r'@\w+', '', text)
    
    # حفظ متن هشتگ و حذف علامت #
    text = text.replace('#', '')
    
    # حذف کاراکترهای نامرئی و ایموجی‌ها (ساده‌سازی شده)
    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
    
    # حذف فاصله‌های اضافی
    text = ' '.join(text.split())
    
    return text

def is_valid_length(text: str, min_length: int = 15) -> bool:
    return len(text.strip()) >= min_length
