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

# デバッグログ機能
def log_debug(msg):
    print(f"DEBUG: {msg}")

def get_drive_service():
    token_info = json.loads(st.secrets["GOOGLE_TOKEN_JSON"])
    creds = Credentials.from_authorized_user_info(token_info, ['https://www.googleapis.com/auth/drive'])
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('drive', 'v3', credentials=creds)

def main():
    st.set_page_config(page_title="行政書士 爆速復習アプリ", layout="wide")
    st.title("🔥 今日の復習リスト")
    
    # AI設定: 古い環境でも通るよう、最も標準的なモデル名に変更
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
            log_debug(f"Target files found: {len(targets)}")
            
            # セッション状態で結果を保持し、再読み込み時のアホな待ち時間を排除
            if 'results' not in st.session_state:
                st.session_state['results'] = {}

            for i, f in enumerate(targets):
                st.subheader(f"📝 項目 {i+1}: {f['name']}")
                
                if f['id'] not in st.session_state['results']:
                    with st.spinner(f"AIが解析中...（初回のみ）"):
                        try:
                            # 画像ダウンロード
                            request = service.files().get_media(fileId=f['id'])
                            fh = io.BytesIO()
                            downloader = MediaIoBaseDownload(fh, request)
                            done = False
                            while not done:
                                _, done = downloader.next_chunk()
                            
                            img_data = Image.open(fh)
                            log_debug(f"Image downloaded: {f['name']}")

                            # 解析実行
                            prompt = "行政書士試験の学習用。画像の内容を要約し、一問一答クイズを3問、日本語で作成せよ。"
                            response = model.generate_content([prompt, img_data])
                            
                            # 結果を保存
                            st.session_state['results'][f['id']] = response.text
                            log_debug(f"AI generation success: {f['name']}")

                        except Exception as e:
                            log_debug(f"ERROR on {f['name']}: {str(e)}")
                            st.error(f"解析失敗: {str(e)}")
                            continue

                # 結果を表示
                st.markdown(st.session_state['results'][f['id']])
                st.divider()

    except Exception as e:
        st.error(f"致命的なエラー: {str(e)}")

if __name__ == "__main__":
    main()
