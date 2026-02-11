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

def analyze_image_direct(image_bytes):
    # ライブラリを使わず、直接APIエンドポイントへPOSTする
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    # 画像をBase64変換
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "行政書士試験の学習用。画像の内容を要約し、一問一答クイズを3問、日本語で作成せよ。"},
                {"inline_data": {"mime_type": "image/jpeg", "data": encoded_image}}
            ]
        }]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    res_json = response.json()
    
    if response.status_code == 200:
        return res_json['candidates'][0]['content']['parts'][0]['text']
    else:
        return f"🚨 API直接通信エラー ({response.status_code}): {json.dumps(res_json)}"

def main():
    st.set_page_config(page_title="行政書士 爆速復習", layout="wide")
    st.title("🔥 今日の復習リスト（直通版）")
    
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
                    with st.spinner("AI直通解析中..."):
                        try:
                            request = service.files().get_media(fileId=f['id'])
                            fh = io.BytesIO()
                            downloader = MediaIoBaseDownload(fh, request)
                            done = False
                            while not done:
                                _, done = downloader.next_chunk()
                            
                            # AIに直接送信
                            result_text = analyze_image_direct(fh.getvalue())
                            st.session_state['results'][f['id']] = result_text
                        except Exception as e:
                            st.error(f"取得失敗: {str(e)}")
                            continue

                st.markdown(st.session_state['results'][f['id']])
                st.divider()

    except Exception as e:
        st.error(f"致命的エラー: {str(e)}")

if __name__ == "__main__":
    main()
