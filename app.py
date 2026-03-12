# ============================================================
# app.py — 在庫アラートツール（Streamlit）
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta, datetime
import io

# ============================================================
# ページ設定
# ============================================================
st.set_page_config(
    page_title="📦 在庫アラートツール",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# カスタムCSS
# ============================================================
st.markdown("""
<style>
/* ヘッダー */
.main-header {
    background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    color: white;
    margin-bottom: 1.5rem;
}
.main-header h1 { margin:0; font-size:1.8rem; }
.main-header p  { margin:0.3rem 0 0; opacity:0.85; font-size:0.95rem; }

/* KPIカード */
.kpi-card {
    background: white;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border-top: 4px solid #1a73e8;
}
.kpi-card.danger  { border-top-color: #e53935; }
.kpi-card.warning { border-top-color: #fb8c00; }
.kpi-card.safe    { border-top-color: #43a047; }

/* アップロードセクション */
.upload-box {
    background: #f8f9fa;
    border: 2px dashed #dee2e6;
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 0.8rem;
}

/* フロー図 */
.flow-box {
    background: linear-gradient(135deg,#e3f2fd,#bbdefb);
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# ユーティリティ関数
# ============================================================

def read_file(file_obj) -> pd.DataFrame:
    """Excel / CSV 自動判定読み込み"""
    if file_obj.name.endswith(".csv"):
        return pd.read_csv(file_obj)
    return pd.read_excel(file_obj)

def assign_alert(stock_days, danger, warning) -> str:
    if pd.isna(stock_days):  return "⚠️ データ不足"
    if stock_days < danger:  return "🔴 危険"
    if stock_days < warning: return "🟡 注意"
    return "🟢 安全"

def style_alert_cell(val) -> str:
    return {
        "🔴 危険":     "background-color:#ffcdd2;color:#b71c1c;font-weight:700;",
        "🟡 注意":     "background-color:#fff8e1;color:#e65100;font-weight:700;",
        "🟢 安全":     "background-color:#e8f5e9;color:#1b5e20;font-weight:700;",
        "⚠️ データ不足":"background-color:#f5f5f5;color:#757575;",
    }.get(val, "")

def generate_dummy_excel(df: pd.DataFrame) -> bytes:
    """DataFrame → Excelバイナリ変換（ダウンロード用）"""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    return buf.getvalue()

# ============================================================
# ヘッダー
# ============================================================
st.markdown("""
<div class="main-header">
  <h1>📦 在庫アラートツール</h1>
  <p>水産・寿司部門向け在庫自動管理プロトタイプ｜出荷・入庫データから在庫日数を自動算出</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 業務フロー表示
# ============================================================
with st.expander("📋 業務フロー・このツールの位置づけ", expanded=False):
    st.markdown("""
<div class="flow-box">
<b>従来フロー</b><br>
受注システム → 販売管理システム → <b>出荷合計表出力</b> → <span style="color:#e53935">在庫帳へ手入力 ← ここを自動化！</span>
<br><br>
<b>新フロー（このツール）</b><br>
出荷合計表CSV/Excel → <b>📦 在庫アラートツールにアップロード</b> → 在庫自動計算・アラート表示
</div>
""", unsafe_allow_html=True)

# ============================================================
# サイドバー：アップロード & 設定
# ============================================================
with st.sidebar:
    st.markdown("## 📂 データアップロード")

    # ─── ダミーデータDLセクション ───
    st.markdown("### 🧪 テスト用ダミーデータ")
    st.caption("初めての方はこちらからサンプルをDLしてアップロードできます")

    # ダミーデータを動的生成
    np.random.seed(42)
    end_date   = datetime.today().date()
    start_date = end_date - timedelta(days=13)
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")

    pm = pd.DataFrame({
        "商品コード":["P001","P002","P003","P004","P005"],
        "商品名":["マグロ赤身（200g）","サーモン（200g）","ハマチ（200g）","甘エビ（100g）","いくら（50g）"]
    })
    ini = pd.DataFrame({
        "商品コード":["P001","P002","P003","P004","P005"],
        "在庫数量":[500,450,300,200,150]
    })
    s_records = []
    for d in date_range:
        for pc in pm["商品コード"]:
            bq = {"P001":40,"P002":35,"P003":25,"P004":20,"P005":15}[pc]
            s_records.append({
                "日付":d.date(),"商品コード":pc,
                "出荷数量":max(0,int(np.random.normal(bq,bq*0.2))),
                "出荷2866数量":max(0,int(np.random.normal(bq*0.3,bq*0.1)))
            })
    s_df = pd.DataFrame(s_records)

    r_records = []
    for pc in pm["商品コード"]:
        br = {"P001":200,"P002":180,"P003":120,"P004":100,"P005":80}[pc]
        for do in [3,7,11]:
            r_records.append({
                "日付":start_date+timedelta(days=do),"商品コード":pc,
                "入庫数量":max(0,int(np.random.normal(br,br*0.1)))
            })
    r_df = pd.DataFrame(r_records).sort_values(["日付","商品コード"]).reset_index(drop=True)

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button("📥 出荷データ",   generate_dummy_excel(s_df), "shipment.xlsx",      key="dl_ship")
        st.download_button("📥 入庫データ",   generate_dummy_excel(r_df), "receipt.xlsx",       key="dl_receipt")
    with col_dl2:
        st.download_button("📥 初期在庫",     generate_dummy_excel(ini),  "initial_stock.xlsx", key="dl_ini")
        st.download_button("📥 商品マスタ",   generate_dummy_excel(pm),   "product_master.xlsx",key="dl_pm")

    st.divider()

    # ─── ファイルアップロード ───
    st.markdown("### 📤 ファイルをアップロード")

    shipment_file      = st.file_uploader("1️⃣ 出荷データ",  type=["xlsx","csv"], key="up_ship",    help="列: 日付/商品コード/出荷数量/出荷2866数量")
    receipt_file       = st.file_uploader("2️⃣ 入庫データ",  type=["xlsx","csv"], key="up_receipt", help="列: 日付/商品コード/入庫数量")
    initial_stock_file = st.file_uploader("3️⃣ 初期在庫",    type=["xlsx","csv"], key="up_ini",     help="列: 商品コード/在庫数量")
    master_file        = st.file_uploader("4️⃣ 商品マスタ",  type=["xlsx","csv"], key="up_master",  help="列: 商品コード/商品名")

    st.divider()

    # ─── アラート設定 ───
    st.markdown("### ⚙️ アラート基準設定")
    danger_threshold  = st.slider("🔴 危険ライン（日数）",  min_value=0.5, max_value=5.0, value=2.0, step=0.5)
    warning_threshold = st.slider("🟡 注意ライン（日数）",  min_value=1.0, max_value=7.0, value=3.0, step=0.5)
    lookback_days     = st.slider("📅 平均日販の計算期間",  min_value=3,   max_value=14,  value=7,   step=1)

# ============================================================
# メイン処理：全ファイルアップロード前
# ============================================================
all_uploaded = all([shipment_file, receipt_file, initial_stock_file, master_file])

if not all_uploaded:
    # ── アップロード進捗 ──
    uploaded_count = sum(bool(f) for f in [shipment_file, receipt_file, initial_stock_file, master_file])
    st.progress(uploaded_count / 4, text=f"アップロード進捗: {uploaded_count}/4 ファイル")

    st.info("👈 左のサイドバーからダミーデータをダウンロードしてアップロードしてください！")

    # フォーマットガイド
    st.markdown("### 📋 Excelファイルのフォーマット")
    tab1, tab2, tab3, tab4 = st.tabs(["出荷データ","入庫データ","初期在庫","商品マスタ"])

    with tab1:
        st.markdown("**shipment.xlsx**")
        st.dataframe(pd.DataFrame({
            "日付":["2025-03-01","2025-03-01","2025-03-02"],
            "商品コード":["P001","P002","P001"],
            "出荷数量":[40,35,42],
            "出荷2866数量":[12,10,11]
        }), hide_index=True, use_container_width=True)

    with tab2:
        st.markdown("**receipt.xlsx**")
        st.dataframe(pd.DataFrame({
            "日付":["2025-03-01","2025-03-04","2025-03-08"],
            "商品コード":["P001","P001","P001"],
            "入庫数量":[200,190,205]
        }), hide_index=True, use_container_width=True)

    with tab3:
        st.markdown("**initial_stock.xlsx**")
        st.dataframe(pd.DataFrame({
            "商品コード":["P001","P002","P003"],
            "在庫数量":[500,450,300]
        }), hide_index=True, use_container_width=True)

    with tab4:
        st.markdown("**product_master.xlsx**")
        st.dataframe(pd.DataFrame({
            "商品コード":["P001","P002","P003"],
            "商品名":["マグロ赤身（200g）","サーモン（200g）","ハマチ（200g）"]
        }), hide_index=True, use_container_width=True)

    st.stop()

# ============================================================
# データ読み込み・計算
# ============================================================
try:
    df_ship    = read_file(shipment_file)
    df_receipt = read_file(receipt_file)
    df_initial = read_file(initial_stock_file)
    df_master  = read_file(master_file)
    df_ship["日付"]    = pd.to_datetime(df_ship["日付"])
    df_receipt["日付"] = pd.to_datetime(df_receipt["日付"])
except Exception as e:
    st.error(f"❌ ファイル読み込みエラー: {e}")
    st.stop()

# 需要 = 出荷数量 + 出荷2866数量
df_ship["需要"] = df_ship["出荷数量"] + df_ship["出荷2866数量"]

latest_date    = df_ship["日付"].max()
lookback_start = latest_date - timedelta(days=lookback_days - 1)

# 平均日販
avg_daily_sales = (
    df_ship[df_ship["日付"] >= lookback_start]
    .groupby("商品コード")["需要"]
    .sum().div(lookback_days)
    .reset_index().rename(columns={"需要":"平均日販"})
)
# 出荷累計
total_shipment = (
    df_ship.groupby("商品コード")["需要"]
    .sum().reset_index().rename(columns={"需要":"出荷累計"})
)
# 入庫累計
total_receipt = (
    df_receipt.groupby("商品コード")["入庫数量"]
    .sum().reset_index().rename(columns={"入庫数量":"入庫累計"})
)
# 結合・現在庫計算
result = (
    df_master
    .merge(df_initial,      on="商品コード", how="left")
    .merge(total_shipment,  on="商品コード", how="left")
    .merge(total_receipt,   on="商品コード", how="left")
    .merge(avg_daily_sales, on="商品コード", how="left")
)
result[["在庫数量","出荷累計","入庫累計","平均日販"]] = \
    result[["在庫数量","出荷累計","入庫累計","平均日販"]].fillna(0)

result["現在庫"] = (result["在庫数量"] + result["入庫累計"] - result["出荷累計"]).clip(lower=0)
result["在庫日数"] = result.apply(
    lambda r: r["現在庫"]/r["平均日販"] if r["平均日販"]>0 else None, axis=1
)
result["アラート"] = result["在庫日数"].apply(
    lambda x: assign_alert(x, danger_threshold, warning_threshold)
)

# ============================================================
# KPI カード
# ============================================================
st.markdown(f"### 📊 在庫状況サマリー（基準日: {latest_date.date()}  ／  計算期間: 直近{lookback_days}日）")

total_p  = len(result)
danger_n = (result["アラート"]=="🔴 危険").sum()
warn_n   = (result["アラート"]=="🟡 注意").sum()
safe_n   = (result["アラート"]=="🟢 安全").sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("📦 総商品数",  f"{total_p} 品")
c2.metric("🔴 危険",      f"{danger_n} 品",  delta=f"在庫日数 < {danger_threshold}日",  delta_color="inverse")
c3.metric("🟡 注意",      f"{warn_n} 品",    delta=f"在庫日数 < {warning_threshold}日", delta_color="off")
c4.metric("🟢 安全",      f"{safe_n} 品",    delta=f"在庫日数 ≥ {warning_threshold}日", delta_color="normal")

st.divider()

# ============================================================
# アラート一覧テーブル
# ============================================================
st.markdown("### 🔔 在庫アラート一覧")

alert_filter = st.radio(
    "表示するアラート",
    ["すべて","🔴 危険のみ","🟡 注意以上","🟢 安全のみ"],
    horizontal=True
)

fmap = {
    "🔴 危険のみ":   result["アラート"]=="🔴 危険",
    "🟡 注意以上":   result["アラート"].isin(["🔴 危険","🟡 注意"]),
    "🟢 安全のみ":   result["アラート"]=="🟢 安全",
}
filtered = result[fmap[alert_filter]] if alert_filter != "すべて" else result.copy()
filtered = filtered.sort_values("在庫日数", ascending=True)

display_df = filtered[["商品コード","商品名","現在庫","平均日販","在庫日数","アラート"]].copy()
display_df["現在庫"]   = display_df["現在庫"].astype(int)
display_df["平均日販"] = display_df["平均日販"].round(1)
display_df["在庫日数"] = display_df["在庫日数"].round(1)

styled = (
    display_df.style
    .applymap(style_alert_cell, subset=["アラート"])
    .format({
        "現在庫":   "{:,}個",
        "平均日販": "{:.1f}個/日",
        "在庫日数": "{:.1f}日",
    })
    .set_properties(**{"text-align":"center"})
)
st.dataframe(styled, use_container_width=True, hide_index=True)

# ============================================================
# 在庫日数バーチャート
# ============================================================
st.divider()
st.markdown("### 📊 商品別 在庫日数チャート")

import altair as alt

chart_df = display_df[["商品名","在庫日数","アラート"]].dropna().copy()
color_map = {"🔴 危険":"#e53935","🟡 注意":"#fb8c00","🟢 安全":"#43a047","⚠️ データ不足":"#9e9e9e"}
chart_df["カラー"] = chart_df["アラート"].map(color_map)

bars = alt.Chart(chart_df).mark_bar(size=35).encode(
    x=alt.X("商品名:N", axis=alt.Axis(labelAngle=-30), sort=None, title="商品名"),
    y=alt.Y("在庫日数:Q", title="在庫日数（日）"),
    color=alt.Color("カラー:N", scale=None, legend=None),
    tooltip=["商品名","在庫日数","アラート"]
)
rule_danger  = alt.Chart(pd.DataFrame({"y":[danger_threshold]})).mark_rule(
    color="#e53935", strokeDash=[6,4], strokeWidth=2).encode(y="y:Q")
rule_warning = alt.Chart(pd.DataFrame({"y":[warning_threshold]})).mark_rule(
    color="#fb8c00", strokeDash=[6,4], strokeWidth=2).encode(y="y:Q")

chart = (bars + rule_danger + rule_warning).properties(height=320)
st.altair_chart(chart, use_container_width=True)
st.caption(f"🔴 赤線: 危険ライン（{danger_threshold}日）　🟡 橙線: 注意ライン（{warning_threshold}日）")

# ============================================================
# 詳細データ
# ============================================================
st.divider()
with st.expander("📂 生データ確認"):
    t1, t2, t3 = st.tabs(["出荷データ","入庫データ","在庫計算詳細"])
    with t1:
        st.dataframe(df_ship.sort_values("日付",ascending=False), hide_index=True, use_container_width=True)
    with t2:
        st.dataframe(df_receipt.sort_values("日付",ascending=False), hide_index=True, use_container_width=True)
    with t3:
        detail = result[["商品コード","商品名","在庫数量","入庫累計","出荷累計","現在庫","平均日販","在庫日数","アラート"]].copy()
        detail.rename(columns={"在庫数量":"初期在庫"}, inplace=True)
        st.dataframe(detail, hide_index=True, use_container_width=True)

# ============================================================
# ダウンロード
# ============================================================
st.divider()
st.markdown("### ⬇️ 結果ダウンロード")

col_d1, col_d2 = st.columns(2)
with col_d1:
    csv = display_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        "📥 CSVでダウンロード",
        csv,
        f"inventory_alert_{latest_date.date()}.csv",
        "text/csv"
    )
with col_d2:
    excel_bytes = generate_dummy_excel(display_df)
    st.download_button(
        "📥 Excelでダウンロード",
        excel_bytes,
        f"inventory_alert_{latest_date.date()}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.divider()
st.caption("📦 在庫アラートツール v1.0 | プロトタイプ版 | 水産・寿司部門向け")
