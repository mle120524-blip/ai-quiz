import streamlit as st
import google.generativeai as genai
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from PIL import Image
import io
import datetime
import json

SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    token_info = json.loads(st.secrets["GOOGLE_TOKEN_JSON"])
    creds = Credentials.from_authorized_user_info(token_info, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('drive', 'v3', credentials=creds)

def main():
    st.set_page_config(page_title="行政書士 爆速復習アプリ", layout="centered")
    st.title("🔥 行政書士 爆速復習")
    
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    try:
        service = get_drive_service()
        folder_id = st.secrets["DRIVE_FOLDER_ID"]
        
        results = service.files().list(q=f"'{folder_id}' in parents and trashed = false", fields="files(id, name, createdTime)").execute()
        files = results.get('files', [])

        today = datetime.datetime.now().date()
        targets = [f for f in files if (today - datetime.datetime.strptime(f['createdTime'][:10], '%Y-%m-%d').date()).days in [0, 1, 3, 7, 30]]

        if not targets:
            st.success("🎉 本日の復習はありません。")
        else:
            st.warning(f"📝 今日は {len(targets)} 件の復習があります。")
            
            if st.button("🚀 今日の全問題を一括で解く"):
                for i, f in enumerate(targets):
                    st.divider()
                    st.subheader(f"第 {i+1} 問: {f['name']}")
                    
                    with st.spinner("画像を読み込んで解析中..."):
                        try:
                            # 【修正ポイント】URLではなく、ドライブから直接バイナリをダウンロード
                            request = service.files().get_media(fileId=f['id'])
                            fh = io.BytesIO()
                            downloader = MediaIoBaseDownload(fh, request)
                            done = False
                            while done is False:
                                status, done = downloader.next_chunk()
                            
                            img_data = Image.open(fh)
                            st.image(img_data, use_container_width=True)
                            
                            prompt = "この画像は行政書士試験の学習資料です。内容を分析し、1.重要論点の要約 2.この内容から予想される一問一答クイズ を日本語で作成してください。"
                            ai_res = model.generate_content([prompt, img_data])
                            
                            st.markdown(ai_res.text)
                        except Exception as ai_err:
                            st.error(f"解析エラー: {str(ai_err)}")

    except Exception as e:
        st.error(f"⚠️ エラー: {str(e)}")

if __name__ == "__main__":
    main()
