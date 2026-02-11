import streamlit as st
import requests
import json
import base64
import io
import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

def get_drive_service():
    token_info = json.loads(st.secrets["GOOGLE_TOKEN_JSON"])
    creds = Credentials.from_authorized_user_info(token_info, ['https://www.googleapis.com/auth/drive'])
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('drive', 'v3', credentials=creds)

def analyze_image_final(image_bytes):
    # 【最重要修正】APIバージョンをv1betaからv1に変更し、404を回避
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "行政書士試験の学習用。画像の内容を要約し、一問一答クイズを3問、日本語で作成せよ。"},
                {"inline_data": {"mime_type": "image/jpeg", "data": encoded_image}}
            ]
        }]
    }
    
    response = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
    res_json = response.json()
    
    if response.status_code == 200:
        return res_json['candidates'][0]['content']['parts'][0]['text']
    else:
        # 万が一のためにエラーの詳細はログに出す
        return f"AI解析に失敗しました。詳細: {response.text}"

def main():
    st.set_page_config(page_title="行政書士 爆速復習", layout="wide")
    st.title("🔥 今日の復習リスト")

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
            if 'results' not in st.session_state:
                st.session_state['results'] = {}

            for i, f in enumerate(targets):
                st.subheader(f"📝 項目 {i+1}: {f['name']}")
                
                if f['id'] not in st.session_state['results']:
                    with st.status(f"項目 {i+1} を解析中...", expanded=True):
                        try:
                            request = service.files().get_media(fileId=f['id'])
                            fh = io.BytesIO()
                            downloader = MediaIoBaseDownload(fh, request)
                            done = False
                            while not done:
                                _, done = downloader.next_chunk()
                            
                            st.session_state['results'][f['id']] = analyze_image_final(fh.getvalue())
                        except Exception as e:
                            st.error(f"取得失敗: {str(e)}")
                            continue

                st.markdown(st.session_state['results'][f['id']])
                st.divider()

    except Exception as e:
        st.error(f"致命的エラー: {str(e)}")

if __name__ == "__main__":
    main()
