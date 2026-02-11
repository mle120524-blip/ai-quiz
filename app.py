import streamlit as st
import requests
import base64
import io

# --- 確定設定 ---
GITHUB_USER = "mle120524-blip"
REPO_NAME = "ai-quiz"
FOLDER_NAME = "images"
API_KEY = st.secrets["GOOGLE_API_KEY"]

st.set_page_config(page_title="行政書士 爆速復習", layout="wide")
st.title("🚀 行政書士 爆速復習（Gemini 2.5 直結）")

# GitHubからファイルリスト取得
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
                        with st.spinner("最新AI (2.5 Flash) が解析中..."):
                            # 画像準備
                            img_res = requests.get(f['download_url'])
                            img_b64 = base64.b64encode(img_res.content).decode('utf-8')
                            
                            # 【修正】あなたの環境で有効な「gemini-2.5-flash」を直接指定
                            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
                            
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
                            else:
                                # 2.5がダメなら2.0、それでもダメなら1.5...と意地でも動かす
                                st.error("予備モデルで再試行します...")
                                fallback_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
                                ai_res = requests.post(fallback_url, json=payload, headers={'Content-Type': 'application/json'})
                                if ai_res.status_code == 200:
                                    st.markdown(ai_res.json()['candidates'][0]['content']['parts'][0]['text'])
                                else:
                                    st.error(f"全滅しました: {ai_res.text}")
    else:
        st.error(f"GitHub接続失敗: {res.status_code}")
except Exception as e:
    st.error(f"エラー: {e}")
