import streamlit as st
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import datetime
import json

# 設定
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    # Secretsから「合鍵」を直接読み込む（ここが重要！）
    token_info = json.loads(st.secrets["GOOGLE_TOKEN_JSON"])
    creds = Credentials.from_authorized_user_info(token_info, SCOPES)
    return build('drive', 'v3', credentials=creds)

def main():
    st.title("📱 行政書士 爆速復習アプリ")
    
    try:
        service = get_drive_service()
        folder_id = st.secrets["DRIVE_FOLDER_ID"]
        
        # ファイル取得
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="files(id, name, createdTime)").execute()
        files = results.get('files', [])

        # 日付判定 (0, 1, 3, 7, 30日)
        today = datetime.datetime.now().date()
        targets = []
        for f in files:
            c_date = datetime.datetime.strptime(f['createdTime'][:10], '%Y-%m-%d').date()
            diff = (today - c_date).days
            if diff in [0, 1, 3, 7, 30]:
                targets.append(f)

        if not targets:
            st.success("本日の復習はありません。")
        else:
            st.write(f"今日の復習対象：{len(targets)}件")
            # ここにクイズ生成ロジックが続きます...
            
    except Exception as e:
        st.error(f"接続エラーが発生しました。設定を再確認してください。")

if __name__ == "__main__":
    main()
