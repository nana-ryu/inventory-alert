# ============================================================
# generate_dummy.py — ダミーデータ生成スクリプト
# ============================================================
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

np.random.seed(42)

os.makedirs("data", exist_ok=True)

end_date   = datetime.today().date()
start_date = end_date - timedelta(days=13)
date_range = pd.date_range(start=start_date, end=end_date, freq="D")

# 商品マスタ
product_master = pd.DataFrame({
    "商品コード": ["P001", "P002", "P003", "P004", "P005"],
    "商品名": [
        "マグロ赤身（200g）",
        "サーモン（200g）",
        "ハマチ（200g）",
        "甘エビ（100g）",
        "いくら（50g）",
    ]
})
product_master.to_excel("data/product_master.xlsx", index=False)

# 初期在庫
initial_stock = pd.DataFrame({
    "商品コード": ["P001", "P002", "P003", "P004", "P005"],
    "在庫数量":   [500,    450,    300,    200,    150]
})
initial_stock.to_excel("data/initial_stock.xlsx", index=False)

# 出荷データ
shipment_records = []
for date in date_range:
    for product_code in product_master["商品コード"]:
        base_qty = {"P001":40,"P002":35,"P003":25,"P004":20,"P005":15}[product_code]
        shipment_qty  = max(0, int(np.random.normal(base_qty, base_qty*0.2)))
        shipment_2866 = max(0, int(np.random.normal(base_qty*0.3, base_qty*0.1)))
        shipment_records.append({
            "日付": date.date(),
            "商品コード": product_code,
            "出荷数量": shipment_qty,
            "出荷2866数量": shipment_2866,
        })
shipment_df = pd.DataFrame(shipment_records)
shipment_df.to_excel("data/shipment.xlsx", index=False)

# 入庫データ
receipt_records = []
for product_code in product_master["商品コード"]:
    base_receipt = {"P001":200,"P002":180,"P003":120,"P004":100,"P005":80}[product_code]
    for day_offset in [3, 7, 11]:
        receipt_date = start_date + timedelta(days=day_offset)
        receipt_qty  = max(0, int(np.random.normal(base_receipt, base_receipt*0.1)))
        receipt_records.append({
            "日付": receipt_date,
            "商品コード": product_code,
            "入庫数量": receipt_qty,
        })
receipt_df = pd.DataFrame(receipt_records).sort_values(["日付","商品コード"]).reset_index(drop=True)
receipt_df.to_excel("data/receipt.xlsx", index=False)

print("✅ ダミーデータ生成完了")
