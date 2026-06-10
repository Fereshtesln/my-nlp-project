from FlagEmbedding import BGEM3FlagModel

class BGEEmbedder:
    def __init__(self, model_name='BAAI/bge-m3'):
        """
        مدل اصلی BGE-M3 برای تولید بردارهای معنایی و کلمات کلیدی.
        این مدل در اولین اجرا دانلود می‌شود (حدود 2.2 گیگابایت).
        """
        print(f"Loading {model_name}...")
        # اگر GPU ندارید از cpu استفاده کنید. اگر دارید 'cuda' قرار دهید.
        self.model = BGEM3FlagModel(model_name, use_fp16=False, device='cpu') 
        print("Model loaded successfully!")

    def encode(self, text):
        """
        تولید همزمان بردارهای Dense و Sparse
        """
        embeddings = self.model.encode(
            [text],
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False
        )

        # استخراج بردارهای مربوط به اولین (و تنها) متن ورودی
                # اصلاح شده برای اطمینان از بازگشت صحیح انواع داده
        return {
            'dense': embeddings['dense_vecs'][0].tolist(),
            'sparse': {int(k): v for k, v in embeddings['lexical_weights'][0].items()}
        }

   