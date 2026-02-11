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
    st.set_page_config(page_title="行政書士 爆速復習アプリ", layout="wide")
    st.title("🔥 今日の復習リスト")
    
    # モデル名を最新の安定版に修正
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
            # 画像は表示せず、いきなり中身を並べる
            for i, f in enumerate(targets):
                with st.container():
                    st.subheader(f"📝 項目 {i+1}: {f['name']}")
                    
                    # セッション状態を使って、一度生成したテキストを保持（再読み込み対策）
                    if f['id'] not in st.session_state:
                        try:
                            request = service.files().get_media(fileId=f['id'])
                            fh = io.BytesIO()
                            downloader = MediaIoBaseDownload(fh, request)
                            done = False
                            while not done:
                                _, done = downloader.next_chunk()
                            
                            img_data = Image.open(fh)
                            prompt = "行政書士試験の学習用です。この画像から『重要論点の要約』と『今日解くべき一問一答クイズ』を3問、簡潔に作成してください。画像は表示しないので、テキストだけで完結させてください。"
                            ai_res = model.generate_content([prompt, img_data])
                            st.session_state[f['id']] = ai_res.text
                        except:
                            st.session_state[f['id']] = "解析エラー：画像が読み込めませんでした。"
                    
                    st.markdown(st.session_state[f['id']])
                    st.divider()

    except Exception as e:
        st.error(f"⚠️ システムエラー: {str(e)}")

if __name__ == "__main__":
    main()
