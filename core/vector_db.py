from qdrant_client import QdrantClient
from qdrant_client.http import models

class QdrantManager:
    def __init__(self, collection_name="tweets_collection", path="qdrant_data"):
        """
        راه‌اندازی Qdrant. برای ذخیره دائمی داده‌ها از مسیر محلی (path) استفاده می‌کنیم.
        """
        self.collection_name = collection_name
        self.client = QdrantClient(path=path)
        
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """
        بررسی می‌کند که آیا کالکشن وجود دارد یا خیر. اگر نبود، آن را با پشتیبانی از بردارهای Dense و Sparse می‌سازد.
        """
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": models.VectorParams(
                        size=1024, # سایز بردار Dense مدل BGE-M3
                        distance=models.Distance.COSINE
                    )
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams()
                }
            )
            print(f"Collection '{self.collection_name}' created.")

    # پارامتر text به ورودی‌ها اضافه شد
    def insert_tweet(self, tweet_id, dense_vec, sparse_vec, timestamp, text):
        """
        ذخیره توییت به همراه بردارهای هیبریدی، زمان انتشار و متن اصلی
        """
        # تبدیل دیکشنری اسپارس به فرمت قابل فهم برای Qdrant
        print("--- Debugging vector_db.py ---")
        print(f"sparse_vec received in search_similar: {sparse_vec}")
        print(f"Type of sparse_vec received: {type(sparse_vec)}")
        print("------------------------------")

        indices = [int(k) for k in sparse_vec.keys()]
        values = list(sparse_vec.values())

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=tweet_id,
                    vector={
                        "dense": dense_vec,
                        "sparse": models.SparseVector(indices=indices, values=values)
                    },
                    payload={
                        "timestamp": timestamp,
                        "text": text  # متن به payload اضافه شد
                    }
                )
            ]
        )

    def search_similar(self, dense_vec, sparse_vec, limit=3):
        from qdrant_client import models
        
        # تبدیل مقادیر numpy به float استاندارد پایتون برای جلوگیری از خطای JSON
        clean_sparse_vec = {k: float(v) for k, v in sparse_vec.items()}
        
        results = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                models.Prefetch(
                    query=dense_vec,
                    using="dense",
                    limit=limit,
                ),
                models.Prefetch(
                    query=models.SparseVector(
                        indices=list(clean_sparse_vec.keys()),
                        values=list(clean_sparse_vec.values())
                    ),
                    using="sparse",
                    limit=limit,
                )
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=limit,
            with_payload=True  # برای برگرداندن payload همراه با نتایج اضافه شد
        )
        return results.points
