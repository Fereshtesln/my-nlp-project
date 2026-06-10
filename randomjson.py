import json
import random

input_file = "input.json"
output_file = "content.json"

# خواندن فایل
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# انتخاب 1000 رکورد تصادفی
sample_size = min(1000, len(data))
sampled = random.sample(data, sample_size)

# ذخیره در فایل جدید
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(sampled, f, ensure_ascii=False, indent=2)

print(f"{sample_size} رکورد تصادفی ذخیره شد در {output_file}")
