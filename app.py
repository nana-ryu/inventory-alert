import streamlit as st

st.title("在庫アラートアプリ")

st.write("アプリ起動テスト")

uploaded_file = st.file_uploader("Excelファイルをアップロード")

if uploaded_file:
    st.success("ファイル読み込み成功")
