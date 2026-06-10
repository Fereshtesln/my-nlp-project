import os
import pickle
from datasketch import MinHash, MinHashLSH

class MinHashMatcher:
    def __init__(self, num_perm=128, threshold=0.85):
        """
        num_perm: تعداد جایگشت‌ها
        threshold: آستانه شباهت (مثلاً 0.85 یعنی 85 درصد شباهت به بالا کپی محسوب شود)
        """
        self.num_perm = num_perm
        # اضافه کردن LSH برای جستجوی سریع
        self.lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)

    def _get_shingles(self, text):
        tokens = text.split()
        return set(tokens)

    def generate_minhash(self, text):
        m = MinHash(num_perm=self.num_perm)
        shingles = self._get_shingles(text)
        for shingle in shingles:
            m.update(shingle.encode('utf8'))
        return m

    def calculate_jaccard(self, minhash1, minhash2):
        return minhash1.jaccard(minhash2)

    def insert(self, doc_id, text):
        """
        تولید MinHash و ذخیره آن در LSH Index با یک شناسه (ID).
        """
        m = self.generate_minhash(text)
        self.lsh.insert(doc_id, m)

    def check_duplicate(self, text):
        """
        بررسی می‌کند که آیا کپی دقیقی از این متن در LSH وجود دارد یا خیر.
        خروجی: در صورت یافتن کپی True و در غیر این صورت False برمی‌گرداند.
        """
        duplicates = self.query(text)
        return len(duplicates) > 0

    def query(self, text):
        """
        تولید MinHash برای متن ورودی و برگرداندن لیست شناسه‌های مشابه از LSH.
        """
        m = self.generate_minhash(text)
        return self.lsh.query(m)

    # --- متدهای جدید برای پایداری داده‌ها (ذخیره روی هارد) ---

    def save(self, filepath="minhash_index.pkl"):
        """
        ذخیره وضعیت فعلی LSH در یک فایل
        """
        with open(filepath, 'wb') as f:
            pickle.dump(self.lsh, f)
        # print(f"MinHash index saved to {filepath}")

    def load(self, filepath="minhash_index.pkl"):
        """
        بارگذاری وضعیت LSH از فایل (در صورت وجود)
        """
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                self.lsh = pickle.load(f)
            print(f"✅ MinHash index loaded successfully from {filepath}")
        else:
            print("⚠️ No existing MinHash index found. Starting a fresh index.")
