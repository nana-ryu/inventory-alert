# ============================================================
# app.py — 在庫アラート＋出荷予測ツール（Streamlit）v2.0
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import timedelta, datetime
import io

# ============================================================
# ページ設定
# ============================================================
st.set_page_config(
    page_title="📦 在庫アラート＋出荷予測ツール",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# カスタムCSS
# ============================================================
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
    padding: 1.5rem 2rem; border-radius: 12px;
    color: white; margin-bottom: 1.5rem;
}
.main-header h1 { margin:0; font-size:1.8rem; }
.main-header p  { margin:0.3rem 0 0; opacity:0.85; font-size:0.95rem; }

.section-card {
    background: white; border-radius: 10px;
    padding: 1.2rem 1.5rem; margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
}
.forecast-header {
    background: linear-gradient(135deg,#00897b,#00695c);
    color:white; padding:0.8rem 1.2rem;
    border-radius:8px; margin-bottom:1rem;
}
.badge-danger  { background:#ffcdd2; color:#b71c1c; padding:3px 10px; border-radius:20px; font-weight:700; font-size:0.85rem; }
.badge-warning { background:#fff8e1; color:#e65100; padding:3px 10px; border-radius:20px; font-weight:700; font-size:0.85rem; }
.badge-safe    { background:#e8f5e9; color:#1b5e20; padding:3px 10px; border-radius:20px; font-weight:700; font-size:0.85rem; }

.legend-box {
    display:flex; gap:1rem; flex-wrap:wrap;
    background:#f8f9fa; border-radius:8px;
    padding:0.6rem 1rem; margin-bottom:0.5rem;
    font-size:0.85rem;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# ユーティリティ関数
# ============================================================

def read_file(file_obj) -> pd.DataFrame:
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
        "🔴 危険":      "background-color:#ffcdd2;color:#b71c1c;font-weight:700;",
        "🟡 注意":      "background-color:#fff8e1;color:#e65100;font-weight:700;",
        "🟢 安全":      "background-color:#e8f5e9;color:#1b5e20;font-weight:700;",
        "⚠️ データ不足":"background-color:#f5f5f5;color:#757575;",
    }.get(val, "")

def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    return buf.getvalue()

# ============================================================
# ヘッダー
# ============================================================
st.markdown("""
<div class="main-header">
  <h1>📦 在庫アラート＋出荷予測ツール <span style="font-size:1rem;opacity:0.8">v2.0</span></h1>
  <p>水産・寿司部門向け在庫管理プロトタイプ｜在庫アラート・週次トレンド・出荷予測を一画面で確認</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# ナビゲーションタブ（最上位）
# ============================================================
main_tab1, main_tab2, main_tab3 = st.tabs([
    "📊 在庫アラート",
    "📈 出荷予測・トレンド",
    "📋 データ確認",
])

# ============================================================
# サイドバー：アップロード & 設定
# ============================================================
with st.sidebar:
    st.markdown("## 📂 データアップロード")

    # ── ダミーデータDL ──
    st.markdown("### 🧪 サンプルデータDL")
    st.caption("初めての方はここからDL→アップロード")

    np.random.seed(42)
    today       = datetime.today().date()
    end_date    = today
    start_date  = today - timedelta(days=13)
    date_range  = pd.date_range(start=start_date, end=end_date, freq="D")
    monday      = today - timedelta(days=today.weekday())
    weeks_list  = [(monday - timedelta(weeks=i)) for i in range(5, -1, -1)]

    base_qty_map = {"P001":40,"P002":35,"P003":25,"P004":20,"P005":15}
    pm = pd.DataFrame({
        "商品コード":["P001","P002","P003","P004","P005"],
        "商品名":["マグロ赤身（200g）","サーモン（200g）","ハマチ（200g）","甘エビ（100g）","いくら（50g）"]
    })
    ini = pd.DataFrame({"商品コード":["P001","P002","P003","P004","P005"],"在庫数量":[500,450,300,200,150]})
    s_rec = []
    for d in date_range:
        for pc in pm["商品コード"]:
            bq = base_qty_map[pc]
            s_rec.append({"日付":d.date(),"商品コード":pc,
                          "出荷数量":max(0,int(np.random.normal(bq,bq*0.2))),
                          "出荷2866数量":max(0,int(np.random.normal(bq*0.3,bq*0.1)))})
    s_df = pd.DataFrame(s_rec)
    r_rec = []
    for pc in pm["商品コード"]:
        br = {"P001":200,"P002":180,"P003":120,"P004":100,"P005":80}[pc]
        for do in [3,7,11]:
            r_rec.append({"日付":start_date+timedelta(days=do),"商品コード":pc,
                          "入庫数量":max(0,int(np.random.normal(br,br*0.1)))})
    r_df = pd.DataFrame(r_rec).sort_values(["日付","商品コード"]).reset_index(drop=True)

    # 週次実績
    act_rec = []
    for pc in pm["商品コード"]:
        bq = base_qty_map[pc]; wbase = bq*7; tf = 1.0
        for w in weeks_list:
            sea = 1+0.1*np.sin(weeks_list.index(w)*np.pi/3)
            act_rec.append({"週":w.strftime("%Y-W%V"),"週開始日":w,"商品コード":pc,
                            "実績数量":max(0,int(np.random.normal(wbase*tf*sea,wbase*0.1)))})
            tf *= np.random.uniform(0.95,1.05)
    act_df = pd.DataFrame(act_rec)

    # 週次計画（実績6週＋未来4週）
    plan_weeks = weeks_list + [(monday+timedelta(weeks=i)) for i in range(1,5)]
    plan_rec = []
    for pc in pm["商品コード"]:
        bq = base_qty_map[pc]; wbase = bq*7
        for w in plan_weeks:
            plan_rec.append({"週":w.strftime("%Y-W%V"),"週開始日":w,"商品コード":pc,
                             "計画数量":int(wbase*np.random.uniform(0.95,1.05))})
    plan_df = pd.DataFrame(plan_rec)

    col1,col2 = st.columns(2)
    with col1:
        st.download_button("📥 出荷",   df_to_excel_bytes(s_df),   "shipment.xlsx",       key="dl_s")
        st.download_button("📥 入庫",   df_to_excel_bytes(r_df),   "receipt.xlsx",        key="dl_r")
        st.download_button("📥 週実績", df_to_excel_bytes(act_df), "weekly_actual.xlsx",  key="dl_a")
    with col2:
        st.download_button("📥 初期在庫", df_to_excel_bytes(ini),     "initial_stock.xlsx",  key="dl_i")
        st.download_button("📥 商品マスタ",df_to_excel_bytes(pm),      "product_master.xlsx", key="dl_pm")
        st.download_button("📥 週計画",  df_to_excel_bytes(plan_df), "weekly_plan.xlsx",    key="dl_p")

    st.divider()

    # ── ファイルアップロード ──
    st.markdown("### 📤 ファイルアップロード")

    st.markdown("**在庫アラート用**")
    shipment_file      = st.file_uploader("1️⃣ 出荷データ",    type=["xlsx","csv"], key="up_s")
    receipt_file       = st.file_uploader("2️⃣ 入庫データ",    type=["xlsx","csv"], key="up_r")
    initial_stock_file = st.file_uploader("3️⃣ 初期在庫",      type=["xlsx","csv"], key="up_i")
    master_file        = st.file_uploader("4️⃣ 商品マスタ",    type=["xlsx","csv"], key="up_m")

    st.markdown("**出荷予測用**")
    actual_file = st.file_uploader("5️⃣ 週次実績データ", type=["xlsx","csv"], key="up_a",
                                   help="列: 週 / 週開始日 / 商品コード / 実績数量")
    plan_file   = st.file_uploader("6️⃣ 週次計画データ", type=["xlsx","csv"], key="up_p",
                                   help="列: 週 / 週開始日 / 商品コード / 計画数量")

    st.divider()

    # ── アラート設定 ──
    st.markdown("### ⚙️ 設定")
    danger_threshold  = st.slider("🔴 危険ライン（日数）",  0.5, 5.0, 2.0, 0.5)
    warning_threshold = st.slider("🟡 注意ライン（日数）",  1.0, 7.0, 3.0, 0.5)
    lookback_days     = st.slider("📅 日販計算期間（日）",  3,   14,  7,   1)
    forecast_weeks    = st.slider("🔮 予測週数（先週数）",  1,   4,   2,   1)

# ============================================================
# 共通：在庫アラート計算
# ============================================================
stock_ready = all([shipment_file, receipt_file, initial_stock_file, master_file])
result      = None
latest_date = None

if stock_ready:
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

    df_ship["需要"] = df_ship["出荷数量"] + df_ship["出荷2866数量"]
    latest_date    = df_ship["日付"].max()
    lookback_start = latest_date - timedelta(days=lookback_days - 1)

    avg_daily_sales = (
        df_ship[df_ship["日付"] >= lookback_start]
        .groupby("商品コード")["需要"].sum().div(lookback_days)
        .reset_index().rename(columns={"需要":"平均日販"})
    )
    total_shipment = (
        df_ship.groupby("商品コード")["需要"].sum()
        .reset_index().rename(columns={"需要":"出荷累計"})
    )
    total_receipt = (
        df_receipt.groupby("商品コード")["入庫数量"].sum()
        .reset_index().rename(columns={"入庫数量":"入庫累計"})
    )
    result = (
        df_master
        .merge(df_initial,      on="商品コード", how="left")
        .merge(total_shipment,  on="商品コード", how="left")
        .merge(total_receipt,   on="商品コード", how="left")
        .merge(avg_daily_sales, on="商品コード", how="left")
    )
    result[["在庫数量","出荷累計","入庫累計","平均日販"]] = \
        result[["在庫数量","出荷累計","入庫累計","平均日販"]].fillna(0)
    result["現在庫"]   = (result["在庫数量"]+result["入庫累計"]-result["出荷累計"]).clip(lower=0)
    result["在庫日数"] = result.apply(
        lambda r: r["現在庫"]/r["平均日販"] if r["平均日販"]>0 else None, axis=1)
    result["アラート"] = result["在庫日数"].apply(
        lambda x: assign_alert(x, danger_threshold, warning_threshold))

# ============================================================
# TAB1：在庫アラート
# ============================================================
with main_tab1:
    if not stock_ready:
        n = sum(bool(f) for f in [shipment_file,receipt_file,initial_stock_file,master_file])
        st.progress(n/4, text=f"アップロード進捗: {n}/4 ファイル")
        st.info("👈 サイドバーから在庫アラート用4ファイルをアップロードしてください")
        st.stop()

    # KPIカード
    st.markdown(f"### 📊 在庫状況サマリー（基準日: {latest_date.date()}）")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("📦 総商品数",  f"{len(result)} 品")
    c2.metric("🔴 危険",  f"{(result['アラート']=='🔴 危険').sum()} 品",  delta=f"< {danger_threshold}日",  delta_color="inverse")
    c3.metric("🟡 注意",  f"{(result['アラート']=='🟡 注意').sum()} 品",  delta=f"< {warning_threshold}日", delta_color="off")
    c4.metric("🟢 安全",  f"{(result['アラート']=='🟢 安全').sum()} 品",  delta=f"≥ {warning_threshold}日", delta_color="normal")

    st.divider()

    # フィルター
    st.markdown("### 🔔 在庫アラート一覧")
    af = st.radio("表示するアラート", ["すべて","🔴 危険のみ","🟡 注意以上","🟢 安全のみ"], horizontal=True)
    fmap = {
        "🔴 危険のみ": result["アラート"]=="🔴 危険",
        "🟡 注意以上": result["アラート"].isin(["🔴 危険","🟡 注意"]),
        "🟢 安全のみ": result["アラート"]=="🟢 安全",
    }
    filtered = result[fmap[af]].copy() if af!="すべて" else result.copy()
    filtered = filtered.sort_values("在庫日数", ascending=True)

    disp = filtered[["商品コード","商品名","現在庫","平均日販","在庫日数","アラート"]].copy()
    disp["現在庫"]   = disp["現在庫"].astype(int)
    disp["平均日販"] = disp["平均日販"].round(1)
    disp["在庫日数"] = disp["在庫日数"].round(1)

    st.dataframe(
        disp.style.applymap(style_alert_cell, subset=["アラート"])
            .format({"現在庫":"{:,}個","平均日販":"{:.1f}個/日","在庫日数":"{:.1f}日"})
            .set_properties(**{"text-align":"center"}),
        use_container_width=True, hide_index=True
    )

    # バーチャート
    st.divider()
    st.markdown("### 📊 商品別 在庫日数チャート")
    chart_df = disp[["商品名","在庫日数","アラート"]].dropna().copy()
    cmap = {"🔴 危険":"#e53935","🟡 注意":"#fb8c00","🟢 安全":"#43a047","⚠️ データ不足":"#9e9e9e"}
    chart_df["カラー"] = chart_df["アラート"].map(cmap)

    bars = alt.Chart(chart_df).mark_bar(size=40).encode(
        x=alt.X("商品名:N", sort=None, axis=alt.Axis(labelAngle=-20), title=""),
        y=alt.Y("在庫日数:Q", title="在庫日数（日）"),
        color=alt.Color("カラー:N", scale=None, legend=None),
        tooltip=["商品名","在庫日数","アラート"]
    )
    r_d = alt.Chart(pd.DataFrame({"y":[danger_threshold]})).mark_rule(
        color="#e53935", strokeDash=[6,3], strokeWidth=2).encode(y="y:Q")
    r_w = alt.Chart(pd.DataFrame({"y":[warning_threshold]})).mark_rule(
        color="#fb8c00", strokeDash=[6,3], strokeWidth=2).encode(y="y:Q")
    st.altair_chart((bars+r_d+r_w).properties(height=300), use_container_width=True)
    st.caption(f"🔴 赤破線: 危険ライン ({danger_threshold}日)　🟡 橙破線: 注意ライン ({warning_threshold}日)")

    # DLボタン
    st.divider()
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button("📥 CSVダウンロード",
            disp.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"),
            f"alert_{latest_date.date()}.csv", "text/csv")
    with col_d2:
        st.download_button("📥 Excelダウンロード",
            df_to_excel_bytes(disp),
            f"alert_{latest_date.date()}.xlsx")

# ============================================================
# TAB2：出荷予測・トレンド
# ============================================================
with main_tab2:

    st.markdown("""
    <div class="forecast-header">
      <b>📈 出荷予測・トレンド分析</b>　｜　週次実績と計画データから今後の需要を予測します
    </div>
    """, unsafe_allow_html=True)

    # ── 予測ロジック説明 ──
    with st.expander("🔍 予測ロジックの説明", expanded=False):
        st.markdown("""
| ステップ | 計算内容 |
|---|---|
| ① 達成率 | `達成率 = 週次実績 ÷ 週次計画`（直近N週の平均） |
| ② トレンド係数 | `トレンド = 直近週実績 ÷ 2週前実績`（前週比成長率） |
| ③ 予測値 | `予測 = 今後の計画 × 達成率 × トレンド係数` |
| ④ 予測在庫日数 | `予測在庫日数 = 現在庫 ÷ (予測需要 ÷ 7)` |
| ⑤ 予測アラート | 予測在庫日数をもとに同基準でアラート判定 |
        """)

    if not (actual_file and plan_file):
        missing = []
        if not actual_file: missing.append("5️⃣ 週次実績データ")
        if not plan_file:   missing.append("6️⃣ 週次計画データ")
        n2 = sum(bool(f) for f in [actual_file, plan_file])
        st.progress(n2/2, text=f"予測データ: {n2}/2 ファイル")
        st.warning(f"👈 サイドバーからアップロードしてください: {', '.join(missing)}")
        st.stop()

    try:
        df_actual = read_file(actual_file)
        df_plan   = read_file(plan_file)
        df_actual["週開始日"] = pd.to_datetime(df_actual["週開始日"])
        df_plan["週開始日"]   = pd.to_datetime(df_plan["週開始日"])
    except Exception as e:
        st.error(f"❌ 予測ファイル読み込みエラー: {e}")
        st.stop()

    # マスタ未アップ時のフォールバック
    master_for_forecast = df_master if stock_ready else pd.DataFrame({
        "商品コード":["P001","P002","P003","P004","P005"],
        "商品名":["マグロ赤身（200g）","サーモン（200g）","ハマチ（200g）","甘エビ（100g）","いくら（50g）"]
    })

    today_ts  = pd.Timestamp(today)
    actual_past = df_actual[df_actual["週開始日"] <= today_ts].copy()
    plan_future = df_plan[df_plan["週開始日"] >  today_ts].copy()
    plan_all    = df_plan.copy()

    # ── 商品選択 ──
    product_list = master_for_forecast["商品コード"].tolist()
    selected_pc  = st.selectbox(
        "🏷️ 分析する商品を選択",
        options=product_list,
        format_func=lambda pc: f"{pc}｜{master_for_forecast.set_index('商品コード')['商品名'].get(pc, pc)}"
    )

    # ── 選択商品のデータ抽出 ──
    act_pc  = actual_past[actual_past["商品コード"]==selected_pc].sort_values("週開始日").copy()
    plan_pc = plan_all[plan_all["商品コード"]==selected_pc].sort_values("週開始日").copy()
    fut_pc  = plan_future[plan_future["商品コード"]==selected_pc].sort_values("週開始日").copy()

    if len(act_pc) == 0:
        st.error("選択した商品の実績データがありません")
        st.stop()

    # ────────────────────────────────────────
    # 予測計算
    # ────────────────────────────────────────

    # ① 実績と計画を結合して達成率を計算
    merged = act_pc.merge(
        plan_pc[["週開始日","計画数量"]], on="週開始日", how="left"
    )
    merged["達成率"] = merged.apply(
        lambda r: r["実績数量"]/r["計画数量"] if r["計画数量"]>0 else np.nan, axis=1
    )

    # ② 直近N週の平均達成率
    recent_achieve = merged["達成率"].dropna().tail(3).mean()
    recent_achieve = recent_achieve if not np.isnan(recent_achieve) else 1.0

    # ③ トレンド係数（直近2週の実績前週比）
    if len(act_pc) >= 2:
        prev_qty    = act_pc["実績数量"].iloc[-2]
        latest_qty  = act_pc["実績数量"].iloc[-1]
        trend_coef  = (latest_qty / prev_qty) if prev_qty > 0 else 1.0
        trend_coef  = max(0.7, min(trend_coef, 1.3))  # ±30%でキャップ
    else:
        trend_coef = 1.0

    # ④ 予測値の計算（未来N週分）
    forecast_rows = []
    for i, row in fut_pc.head(forecast_weeks).iterrows():
        pred_qty = row["計画数量"] * recent_achieve * trend_coef
        forecast_rows.append({
            "週開始日":   row["週開始日"],
            "週":         row["週"],
            "予測数量":   round(pred_qty),
            "計画数量":   row["計画数量"],
            "予測日販":   round(pred_qty / 7, 1),
        })
    forecast_df = pd.DataFrame(forecast_rows)

    # ⑤ 予測在庫日数（在庫アラートデータがある場合）
    if result is not None and not forecast_df.empty:
        row_r = result[result["商品コード"]==selected_pc]
        if not row_r.empty and not forecast_df.empty:
            curr_stock   = float(row_r["現在庫"].values[0])
            forecast_avg = forecast_df["予測日販"].mean()
            pred_stock_days = curr_stock / forecast_avg if forecast_avg > 0 else None
            pred_alert      = assign_alert(pred_stock_days, danger_threshold, warning_threshold)
        else:
            pred_stock_days = None
            pred_alert      = "⚠️ データ不足"
    else:
        pred_stock_days = None
        pred_alert      = "⚠️ 在庫データ未読込"

    # ────────────────────────────────────────
    # 予測KPIカード
    # ────────────────────────────────────────
    prod_name = master_for_forecast.set_index("商品コード")["商品名"].get(selected_pc, selected_pc)
    st.markdown(f"#### 📌 {selected_pc}｜{prod_name}")

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("📊 達成率（直近3週平均）", f"{recent_achieve*100:.1f}%",
              delta="計画比" , delta_color="off")
    k2.metric("📈 トレンド係数（前週比）", f"{trend_coef*100:.1f}%",
              delta="↑上昇" if trend_coef>1 else "↓下降", delta_color="normal" if trend_coef>1 else "inverse")
    if not forecast_df.empty:
        k3.metric("🔮 次週予測数量", f"{forecast_df['予測数量'].iloc[0]:,}個",
                  delta=f"計画比 {(forecast_df['予測数量'].iloc[0]/forecast_df['計画数量'].iloc[0]-1)*100:+.1f}%" if forecast_df['計画数量'].iloc[0]>0 else "")
    else:
        k3.metric("🔮 次週予測数量", "未来計画データなし")
    if pred_stock_days is not None:
        k4.metric("📦 予測在庫日数", f"{pred_stock_days:.1f}日", delta=pred_alert, delta_color="off")
    else:
        k4.metric("📦 予測在庫日数", "計算不可")

    st.divider()

    # ────────────────────────────────────────
    # トレンドチャート（実績・計画・予測）
    # ────────────────────────────────────────
    st.markdown("### 📉 週次トレンドチャート（実績 vs 計画 vs 予測）")

    # チャート用データ結合
    chart_act  = act_pc[["週開始日","実績数量"]].copy();  chart_act["種別"] = "実績"
    chart_act.rename(columns={"実績数量":"数量"}, inplace=True)

    chart_plan = plan_pc[["週開始日","計画数量"]].copy(); chart_plan["種別"] = "計画"
    chart_plan.rename(columns={"計画数量":"数量"}, inplace=True)

    chart_all  = pd.concat([chart_act, chart_plan], ignore_index=True)

    # ベースライン（実績の最終週から予測につなぐ）
    if not forecast_df.empty:
        # 予測ラインを実績の最終値から繋ぐ
        bridge = pd.DataFrame([{
            "週開始日": act_pc["週開始日"].iloc[-1],
            "数量":     act_pc["実績数量"].iloc[-1],
            "種別":     "予測"
        }])
        chart_forecast = forecast_df[["週開始日","予測数量"]].copy()
        chart_forecast.rename(columns={"予測数量":"数量"}, inplace=True)
        chart_forecast["種別"] = "予測"
        chart_forecast = pd.concat([bridge, chart_forecast], ignore_index=True)
        chart_all = pd.concat([chart_all, chart_forecast], ignore_index=True)

    # 現在日の縦線用
    today_line = pd.DataFrame({"x": [pd.Timestamp(today)]})

    # 色・スタイル定義
    color_scale = alt.Scale(
        domain=["実績","計画","予測"],
        range= ["#1a73e8","#fb8c00","#43a047"]
    )
    dash_scale = alt.Scale(
        domain=["実績","計画","予測"],
        range= [[1,0],[6,3],[4,2]]
    )

    line_chart = alt.Chart(chart_all).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X("週開始日:T", title="週開始日", axis=alt.Axis(format="%m/%d", labelAngle=-30)),
        y=alt.Y("数量:Q",     title="数量（個/週）"),
        color=alt.Color("種別:N", scale=color_scale, legend=alt.Legend(title="凡例")),
        strokeDash=alt.StrokeDash("種別:N", scale=dash_scale),
        tooltip=["種別","週開始日:T","数量"]
    )

    today_rule = alt.Chart(today_line).mark_rule(
        color="#9e9e9e", strokeDash=[4,3], strokeWidth=1.5
    ).encode(x="x:T")

    today_text = alt.Chart(today_line).mark_text(
        text="今日", color="#9e9e9e", dy=-8, fontSize=11
    ).encode(x="x:T")

    full_chart = (line_chart + today_rule + today_text).properties(height=350)
    st.altair_chart(full_chart, use_container_width=True)

    # 凡例説明
    st.markdown("""
<div class="legend-box">
  <span>🔵 <b>実績</b>: 週次の実際の出荷数量</span>
  <span>🟠 <b>計画</b>: 週次の計画出荷数量</span>
  <span>🟢 <b>予測</b>: 達成率×トレンドで補正した予測値</span>
  <span>⬜ 縦線: 現在日</span>
</div>
""", unsafe_allow_html=True)

    st.divider()

    # ────────────────────────────────────────
    # 実績 vs 計画 達成率テーブル
    # ────────────────────────────────────────
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("### 📋 週次実績 vs 計画 比較テーブル")
        table_df = merged[["週","実績数量","計画数量","達成率"]].copy()
        table_df["乖離数量"]  = table_df["実績数量"] - table_df["計画数量"]
        table_df["達成率表示"] = table_df["達成率"].apply(
            lambda x: f"{x*100:.1f}%" if not np.isnan(x) else "-"
        )
        table_df["乖離判定"] = table_df["達成率"].apply(
            lambda x: "🔴 下回り" if x<0.9 else ("🟡 やや下回り" if x<0.97 else ("🟢 達成" if x>=0.97 else "-"))
            if not np.isnan(x) else "-"
        )

        styled_t = (
            table_df[["週","実績数量","計画数量","乖離数量","達成率表示","乖離判定"]]
            .style
            .applymap(style_alert_cell, subset=["乖離判定"])
            .format({"実績数量":"{:,}","計画数量":"{:,}","乖離数量":"{:+,}"})
            .set_properties(**{"text-align":"center"})
        )
        st.dataframe(styled_t, use_container_width=True, hide_index=True)

    with col_right:
        st.markdown("### 🔮 予測テーブル")
        if not forecast_df.empty:
            fc_disp = forecast_df[["週","予測数量","計画数量"]].copy()
            fc_disp["予測vs計画"] = fc_disp.apply(
                lambda r: f"{(r['予測数量']/r['計画数量']-1)*100:+.1f}%" if r["計画数量"]>0 else "-",
                axis=1
            )
            fc_disp["予測日販"] = forecast_df["予測日販"].apply(lambda x: f"{x:.1f}個/日")
            st.dataframe(
                fc_disp.style.format({"予測数量":"{:,}個","計画数量":"{:,}個"})
                       .set_properties(**{"text-align":"center"}),
                use_container_width=True, hide_index=True
            )

            # 予測在庫アラートボックス
            st.markdown("#### 📦 予測在庫アラート")
            alert_color = {
                "🔴 危険":      "#ffcdd2",
                "🟡 注意":      "#fff8e1",
                "🟢 安全":      "#e8f5e9",
                "⚠️ データ不足": "#f5f5f5",
            }.get(pred_alert, "#f5f5f5")
            alert_text_color = {
                "🔴 危険":      "#b71c1c",
                "🟡 注意":      "#e65100",
                "🟢 安全":      "#1b5e20",
                "⚠️ データ不足": "#757575",
            }.get(pred_alert, "#757575")

            st.markdown(f"""
<div style="background:{alert_color};border-radius:10px;padding:1rem;text-align:center;margin-top:0.5rem;">
  <div style="font-size:2rem;">{pred_alert}</div>
  <div style="color:{alert_text_color};font-weight:700;font-size:1.1rem;margin-top:0.3rem;">
    予測在庫日数: {f"{pred_stock_days:.1f}日" if pred_stock_days else "計算不可"}
  </div>
  <div style="color:{alert_text_color};font-size:0.85rem;margin-top:0.2rem;">
    ※ 現在庫 ÷ 予測平均日販で算出
  </div>
</div>
""", unsafe_allow_html=True)
        else:
            st.info("未来週の計画データがありません")

    # ────────────────────────────────────────
    # 全商品サマリー予測テーブル
    # ────────────────────────────────────────
    st.divider()
    st.markdown("### 🌐 全商品 出荷予測サマリー")

    summary_rows = []
    for pc in product_list:
        pn = master_for_forecast.set_index("商品コード")["商品名"].get(pc, pc)
        a  = df_actual[df_actual["商品コード"]==pc].sort_values("週開始日")
        p  = df_plan[df_plan["商品コード"]==pc].sort_values("週開始日")
        pf = p[p["週開始日"] > today_ts]

        m2 = a.merge(p[["週開始日","計画数量"]], on="週開始日", how="left")
        m2["達成率"] = m2.apply(lambda r: r["実績数量"]/r["計画数量"] if r["計画数量"]>0 else np.nan, axis=1)
        ra = m2["達成率"].dropna().tail(3).mean()
        ra = ra if not np.isnan(ra) else 1.0

        if len(a) >= 2:
            tc = a["実績数量"].iloc[-1]/a["実績数量"].iloc[-2] if a["実績数量"].iloc[-2]>0 else 1.0
            tc = max(0.7, min(tc, 1.3))
        else:
            tc = 1.0

        next_plan = pf["計画数量"].iloc[0] if len(pf)>0 else 0
        next_pred = round(next_plan * ra * tc)

        stock_days_pred = None
        alert_pred      = "⚠️"
        if result is not None:
            rr = result[result["商品コード"]==pc]
            if not rr.empty and next_pred > 0:
                cs = float(rr["現在庫"].values[0])
                stock_days_pred = cs / (next_pred/7)
                alert_pred = assign_alert(stock_days_pred, danger_threshold, warning_threshold)

        summary_rows.append({
            "商品コード":  pc,
            "商品名":      pn,
            "達成率":      f"{ra*100:.1f}%",
            "トレンド":    f"{tc*100:.1f}%",
            "次週計画":    f"{next_plan:,}個",
            "次週予測":    f"{next_pred:,}個",
            "予測在庫日数": f"{stock_days_pred:.1f}日" if stock_days_pred else "-",
            "予測アラート": alert_pred,
        })

    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(
        summary_df.style.applymap(style_alert_cell, subset=["予測アラート"])
                  .set_properties(**{"text-align":"center"}),
        use_container_width=True, hide_index=True
    )

# ============================================================
# TAB3：データ確認
# ============================================================
with main_tab3:
    st.markdown("### 📂 アップロードデータ確認")
    tabs_data = st.tabs(["出荷","入庫","初期在庫","商品マスタ","週次実績","週次計画"])

    def safe_show(file_obj, tab):
        with tab:
            if file_obj:
                df_tmp = read_file(file_obj)
                st.dataframe(df_tmp, use_container_width=True, hide_index=True)
            else:
                st.info("データ未アップロード")

    safe_show(shipment_file,      tabs_data[0])
    safe_show(receipt_file,       tabs_data[1])
    safe_show(initial_stock_file, tabs_data[2])
    safe_show(master_file,        tabs_data[3])
    safe_show(actual_file,        tabs_data[4])
    safe_show(plan_file,          tabs_data[5])

# ============================================================
# フッター
# ============================================================
st.divider()
st.caption("📦 在庫アラート＋出荷予測ツール v2.0 | プロトタイプ版 | 水産・寿司部門向け")
