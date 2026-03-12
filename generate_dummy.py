# ============================================================
# generate_dummy.py — ダミーデータ生成スクリプト（出荷予測対応版）
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
    "商品コード": ["P001","P002","P003","P004","P005"],
    "商品名":     ["マグロ赤身（200g）","サーモン（200g）","ハマチ（200g）","甘エビ（100g）","いくら（50g）"]
})
product_master.to_excel("data/product_master.xlsx", index=False)

# 初期在庫
initial_stock = pd.DataFrame({
    "商品コード": ["P001","P002","P003","P004","P005"],
    "在庫数量":   [500,450,300,200,150]
})
initial_stock.to_excel("data/initial_stock.xlsx", index=False)

# 出荷データ
base_qty_map = {"P001":40,"P002":35,"P003":25,"P004":20,"P005":15}
s_records = []
for d in date_range:
    for pc in product_master["商品コード"]:
        bq = base_qty_map[pc]
        s_records.append({
            "日付": d.date(), "商品コード": pc,
            "出荷数量":     max(0, int(np.random.normal(bq, bq*0.2))),
            "出荷2866数量": max(0, int(np.random.normal(bq*0.3, bq*0.1))),
        })
pd.DataFrame(s_records).to_excel("data/shipment.xlsx", index=False)

# 入庫データ
r_records = []
for pc in product_master["商品コード"]:
    br = {"P001":200,"P002":180,"P003":120,"P004":100,"P005":80}[pc]
    for do in [3,7,11]:
        r_records.append({
            "日付": start_date+timedelta(days=do), "商品コード": pc,
            "入庫数量": max(0, int(np.random.normal(br, br*0.1)))
        })
pd.DataFrame(r_records).sort_values(["日付","商品コード"]).reset_index(drop=True).to_excel("data/receipt.xlsx", index=False)

# ─────────────────────────────────────────────
# 週次実績データ（直近6週）
# ─────────────────────────────────────────────
today = datetime.today().date()
# 今週月曜日を起点に6週前まで遡る
monday = today - timedelta(days=today.weekday())
weeks  = [(monday - timedelta(weeks=i)) for i in range(5, -1, -1)]  # 古い順

actual_records = []
for pc in product_master["商品コード"]:
    bq = base_qty_map[pc]
    weekly_base = bq * 7  # 週ベース需要の基準
    trend_factor = 1.0
    for w in weeks:
        week_label = w.strftime("%Y-W%V")
        # 週ごとに微妙な季節変動を追加
        seasonal = 1 + 0.1 * np.sin(weeks.index(w) * np.pi / 3)
        actual_qty = max(0, int(np.random.normal(weekly_base * trend_factor * seasonal, weekly_base * 0.1)))
        trend_factor *= np.random.uniform(0.95, 1.05)  # ゆるやかなトレンド変化
        actual_records.append({
            "週":         week_label,
            "週開始日":   w,
            "商品コード": pc,
            "実績数量":   actual_qty,
        })

actual_df = pd.DataFrame(actual_records)
actual_df.to_excel("data/weekly_actual.xlsx", index=False)

# ─────────────────────────────────────────────
# 週次計画データ（直近6週＋今後4週）
# ─────────────────────────────────────────────
plan_weeks = weeks + [(monday + timedelta(weeks=i)) for i in range(1, 5)]  # 今後4週追加

plan_records = []
for pc in product_master["商品コード"]:
    bq = base_qty_map[pc]
    weekly_base = bq * 7
    for w in plan_weeks:
        week_label = w.strftime("%Y-W%V")
        # 計画はより安定した数値
        plan_qty = int(weekly_base * np.random.uniform(0.95, 1.05))
        plan_records.append({
            "週":         week_label,
            "週開始日":   w,
            "商品コード": pc,
            "計画数量":   plan_qty,
        })

plan_df = pd.DataFrame(plan_records)
plan_df.to_excel("data/weekly_plan.xlsx", index=False)

print("✅ 全ダミーデータ生成完了（出荷予測対応版）")
print(f"  週次実績: {len(actual_df)}行（{len(weeks)}週 × {len(product_master)}商品）")
print(f"  週次計画: {len(plan_df)}行（{len(plan_weeks)}週 × {len(product_master)}商品）")
