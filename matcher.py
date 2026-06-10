from datasketch import MinHash, MinHashLSH
#ین فایل کلاس پایه را نگه می‌دارد تا هر دو اسکریپت از آن استفاده کنند.
class PersistentMinHashMatcher:
    def __init__(self, num_perm=128, threshold=0.8):
        self.num_perm = num_perm
        
        # استفاده از basename ثابت برای اتصال به یک ایندکس مشخص در Redis
        self.lsh = MinHashLSH(
            threshold=threshold, 
            num_perm=num_perm,
            storage_config={
                'type': 'redis',
                'redis': {'host': 'localhost', 'port': 6379, 'db': 0},
                'basename': b'tweets_lsh_index' 
            }
        )

    def _get_shingles(self, text, n=4):
        text = text.lower()
        return set([text[i:i+n] for i in range(len(text) - n + 1)])

    def generate_minhash(self, text):
        m = MinHash(num_perm=self.num_perm)
        for shingle in self._get_shingles(text):
            m.update(shingle.encode('utf8'))
        return m

    def insert(self, doc_id, text):
        m = self.generate_minhash(text)
        self.lsh.insert(doc_id, m)

    def query(self, text):
        m = self.generate_minhash(text)
        return self.lsh.query(m)
