import streamlit as st
import requests
import json
import base64
import io

# --- 基本設定 ---
GITHUB_USER = "mle120524-blip"
REPO_NAME = "ai-quiz"
FOLDER_NAME = "images"
API_KEY = st.secrets["GOOGLE_API_KEY"]

st.set_page_config(page_title="行政書士 爆速復習", layout="wide")
st.title("🚀 行政書士 爆速復習（最終解決版）")

# 1. GitHubからファイルリスト取得
api_url = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/contents/{FOLDER_NAME}"

try:
    res = requests.get(api_url)
    if res.status_code == 200:
        image_files = [f for f in res.json() if f['name'].lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not image_files:
            st.info("📂 imagesフォルダに画像を入れてください。")
        else:
            for f in image_files:
                with st.expander(f"📖 項目: {f['name']}"):
                    if st.button("この問題を解析", key=f['sha']):
                        with st.spinner("AI解析中..."):
                            # 画像の準備
                            img_res = requests.get(f['download_url'])
                            img_b64 = base64.b64encode(img_res.content).decode('utf-8')
                            
                            # 【修正】複数のモデル名を順番に試す（環境によって名称が違うため）
                            # 1.5-flash-001 は最も安定して動く個体識別名です
                            candidate_models = ["gemini-1.5-flash-001", "gemini-1.5-flash", "gemini-pro-vision"]
                            
                            success = False
                            for model_name in candidate_models:
                                url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={API_KEY}"
                                payload = {
                                    "contents": [{
                                        "parts": [
                                            {"text": "行政書士試験の学習用。画像の内容を要約し、一問一答を3問、日本語で作成せよ。"},
                                            {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
                                        ]
                                    }]
                                }
                                ai_res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
                                
                                if ai_res.status_code == 200:
                                    st.markdown(ai_res.json()['candidates'][0]['content']['parts'][0]['text'])
                                    success = True
                                    break # 成功したら抜ける
                            
                            if not success:
                                st.error(f"全てのモデル試行に失敗。最新エラー: {ai_res.text}")
                                # デバッグ：今使えるモデルを一覧表示する
                                list_url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"
                                list_res = requests.get(list_url).json()
                                st.write("【管理者用デバッグ】現在あなたのキーで利用可能なモデル一覧:")
                                st.json(list_res)

    else:
        st.error(f"GitHub接続失敗: {res.status_code}")
except Exception as e:
    st.error(f"エラー: {e}")
