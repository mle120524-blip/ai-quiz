import streamlit as st
import requests
import google.generativeai as genai
from PIL import Image
import io

# --- 確定設定（あなたの環境に完全一致させています） ---
GITHUB_USER = "mle120524-blip"
REPO_NAME = "ai-quiz"
BRANCH = "main"
FOLDER_NAME = "images"
# ---------------------------------------------------------

# AIの設定
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="行政書士 爆速復習", layout="wide")
st.title("🚀 行政書士 爆速復習（GitHub自動取得版）")

# GitHub APIでフォルダ内のファイル一覧を取得
api_url = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/contents/{FOLDER_NAME}"

try:
    # GitHubから画像リストを取得
    response = requests.get(api_url)
    if response.status_code == 200:
        files = response.json()
        image_files = [f for f in files if f['name'].lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not image_files:
            st.info(f"📂 {FOLDER_NAME} フォルダに画像が見つかりません。画像をアップしてください。")
        else:
            st.warning(f"📝 {len(image_files)} 件の復習対象が見つかりました。")
            
            for f in image_files:
                img_name = f['name']
                raw_url = f['download_url'] # 直リンク
                
                with st.expander(f"📖 項目: {img_name}", expanded=False):
                    if st.button(f"この問題を解析する", key=img_name):
                        with st.spinner("AIが解析中..."):
                            # 画像をGitHubから直接読み込む
                            img_res = requests.get(raw_url)
                            img_data = Image.open(io.BytesIO(img_res.content))
                            
                            # AIに解析させる
                            prompt = "行政書士試験の学習用。この画像から『重要論点の要約』と『一問一答クイズを3問』を、画像がなくても理解できる形式で作成してください。"
                            ai_res = model.generate_content([prompt, img_data])
                            st.markdown(ai_res.text)
    else:
        st.error("GitHubリポジトリにアクセスできません。Public設定になっているか確認してください。")

except Exception as e:
    st.error(f"システムエラー: {e}")
