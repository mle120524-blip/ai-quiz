import streamlit as st
import requests
import json
import base64
import io

# --- 確定設定 ---
GITHUB_USER = "mle120524-blip"
REPO_NAME = "ai-quiz"
FOLDER_NAME = "images"

st.set_page_config(page_title="行政書士 爆速復習", layout="wide")
st.title("🚀 行政書士 爆速復習（直通版）")

# 1. GitHubからファイルリスト取得
api_url = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/contents/{FOLDER_NAME}"

try:
    res = requests.get(api_url)
    if res.status_code == 200:
        files = res.json()
        image_files = [f for f in files if f['name'].lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not image_files:
            st.info("📂 imagesフォルダに画像を入れてください。")
        else:
            for f in image_files:
                with st.expander(f"📖 項目: {f['name']}"):
                    if st.button("この問題を解析", key=f['sha']):
                        # --- ここからライブラリを使わないAI呼び出し ---
                        with st.spinner("AI直通解析中..."):
                            try:
                                # 画像を取得してBase64に変換
                                img_res = requests.get(f['download_url'])
                                img_base64 = base64.b64encode(img_res.content).decode('utf-8')
                                
                                # AIへの直通URL（v1 安定版を強制指定）
                                api_key = st.secrets["GOOGLE_API_KEY"]
                                gemini_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
                                
                                payload = {
                                    "contents": [{
                                        "parts": [
                                            {"text": "行政書士試験の学習用。画像の内容を要約し、一問一答クイズを3問、日本語で作成せよ。"},
                                            {"inline_data": {"mime_type": "image/jpeg", "data": img_base64}}
                                        ]
                                    }]
                                }
                                
                                # 送信
                                ai_res = requests.post(gemini_url, json=payload, headers={'Content-Type': 'application/json'})
                                ai_json = ai_res.json()
                                
                                if ai_res.status_code == 200:
                                    st.markdown(ai_json['candidates'][0]['content']['parts'][0]['text'])
                                else:
                                    st.error(f"APIエラー: {ai_json.get('error', {}).get('message', '不明なエラー')}")
                            except Exception as e:
                                st.error(f"処理失敗: {e}")
    else:
        st.error(f"GitHub接続失敗: {res.status_code}")
except Exception as e:
    st.error(f"エラー: {e}")
