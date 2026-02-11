import streamlit as st
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime, timedelta
import io
from PIL import Image
import os  # ← これを必ず追加してください

# --- 定数設定 ---
API_KEY = "AIzaSyAVqTlgomBBGzOMFFwCTFBVj2hcafmIV88"
DRIVE_FOLDER_ID = "あなたのGoogleドライブのフォルダID" # ←ここを書き換え
LOG_FILE_NAME = "review_log.csv"
SCOPES = ['https://www.googleapis.com/auth/drive']

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Googleドライブ認証 ---
def get_drive_service():
    import json
    # すでにSecretsに貼ってくれた「合鍵」をここで読み込みます
    token_info = json.loads(st.secrets["GOOGLE_TOKEN_JSON"])
    creds = Credentials.from_authorized_user_info(token_info, SCOPES)
    
    # 読み込んだ合鍵でドライブに接続します
    return build('drive', 'v3', credentials=creds)
    
service = get_drive_service()

# --- フォルダ内の画像取得とスケジュール管理 ---
def sync_and_get_targets():
    results = service.files().list(
        q=f"'{DRIVE_FOLDER_ID}' in parents and trashed = false",
        fields="files(id, name, createdTime)").execute()
    files = results.get('files', [])
    
    today = datetime.now().date()
    targets = []
    
    for f in files:
        # 作成日から 0, 1, 3, 7, 30日後を判定
        created_date = datetime.strptime(f['createdTime'][:10], '%Y-%m-%d').date()
        diff = (today - created_date).days
        if diff in [0, 1, 3, 7, 30]:
            targets.append(f)
    return targets

# --- UI ---
st.title("📱 行政書士 爆速復習アプリ")
st.write("Googleドライブと同期中...")

targets = sync_and_get_targets()

if not targets:
    st.success("本日の復習はありません。")
else:
    for f in targets:
        with st.expander(f"📖 問題: {f['name']}"):
            # ドライブから画像を直接読み込み
            request = service.files().get_media(fileId=f['id'])
            fh = io.BytesIO(request.execute())
            img = Image.open(fh)
            st.image(img, use_container_width=True)
            
            if st.button("AIクイズ生成", key=f['id']):
                with st.spinner("思考中..."):
                    res = model.generate_content(["この画像から一問一答を3問作成してください。", img])

                    st.info(res.text)

