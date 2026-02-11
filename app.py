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
    
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # 404エラー対策のため、安定版のモデル名を指定
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    try:
        service = get_drive_service()
        folder_id = st.secrets["DRIVE_FOLDER_ID"]
        
        results = service.files().list(q=f"'{folder_id}' in parents and trashed = false", fields="files(id, name, createdTime)").execute()
        files = results.get('files', [])

        now = datetime.datetime.now()
        today = now.date()
        
        # 復習対象の選別
        targets = [f for f in files if (today - datetime.datetime.strptime(f['createdTime'][:10], '%Y-%m-%d').date()).days in [0, 1, 3, 7, 30]]

        if not targets:
            st.success("🎉 本日の復習はありません。")
        else:
            # 本番運用を想定：朝6時以降にまだ生成されていなければ生成を開始
            st.info(f"📅 {today} の学習内容を準備しています...")
            
            for i, f in enumerate(targets):
                # セッション内で「生成済み」かチェック
                if f['id'] not in st.session_state:
                    with st.status(f"項目 {i+1} を解析中...", expanded=False):
                        try:
                            # ドライブからデータを確実にダウンロード
                            request = service.files().get_media(fileId=f['id'])
                            fh = io.BytesIO()
                            downloader = MediaIoBaseDownload(fh, request)
                            done = False
                            while not done:
                                _, done = downloader.next_chunk()
                            
                            img_data = Image.open(fh)
                            prompt = "行政書士試験の学習用です。この画像の内容から『重要論点の要約』と『今日解くべき一問一答クイズ3問』を、画像を見なくても理解できるテキスト形式で日本語で作成してください。"
                            ai_res = model.generate_content([prompt, img_data])
                            
                            # 成功したらセッションに保存
                            st.session_state[f['id']] = ai_res.text
                        except Exception as e:
                            st.session_state[f['id']] = f"解析エラー: {str(e)}"
                
                # 表示部分
                with st.container():
                    st.subheader(f"📝 項目 {i+1}: {f['name']}")
                    st.markdown(st.session_state[f['id']])
                    st.divider()

    except Exception as e:
        st.error(f"⚠️ システムエラー: {str(e)}")

if __name__ == "__main__":
    main()
