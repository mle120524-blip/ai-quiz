import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request  # これが自動更新に必要
import datetime
import json

# 設定
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    token_info = json.loads(st.secrets["GOOGLE_TOKEN_JSON"])
    creds = Credentials.from_authorized_user_info(token_info, SCOPES)
    
    # 【ここが重要】期限が切れていたら、自動で更新する
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        
    return build('drive', 'v3', credentials=creds)

def main():
    st.title("📱 行政書士 爆速復習アプリ")
    
    try:
        # AIの設定
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        service = get_drive_service()
        folder_id = st.secrets["DRIVE_FOLDER_ID"]
        
        # ファイルリスト取得
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="files(id, name, createdTime)").execute()
        files = results.get('files', [])

        today = datetime.datetime.now().date()
        targets = []
        for f in files:
            c_date = datetime.datetime.strptime(f['createdTime'][:10], '%Y-%m-%d').date()
            diff = (today - c_date).days
            if diff in [0, 1, 3, 7, 30]:
                targets.append(f)

        if not targets:
            st.success("本日の復習対象はありません。")
        else:
            st.write(f"本日の対象画像: {len(targets)}枚")
            for f in targets:
                st.image(f"https://drive.google.com/uc?id={f['id']}", caption=f['name'])
                # ここでAIに問題を生成させる
                st.info(f"AIが問題を生成中... ({f['name']})")
                
    except Exception as e:
        # エラーの正体を隠さず表示します
        st.error(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main()
