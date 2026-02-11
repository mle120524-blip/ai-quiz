import streamlit as st
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import datetime
import json

# 設定
# あなたのtokenに合わせて権限を修正済み
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    # Secretsから合鍵を読み込む
    token_info = json.loads(st.secrets["GOOGLE_TOKEN_JSON"])
    creds = Credentials.from_authorized_user_info(token_info, SCOPES)
    
    # 期限が切れていたら、リフレッシュトークンを使って自動で更新する
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        
    return build('drive', 'v3', credentials=creds)

def main():
    st.set_page_config(page_title="行政書士 爆速復習アプリ", layout="centered")
    st.title("📱 行政書士 爆速復習アプリ")
    
    # AIの初期設定
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    try:
        service = get_drive_service()
        folder_id = st.secrets["DRIVE_FOLDER_ID"]
        
        # 指定フォルダ内の画像を取得
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name, createdTime)").execute()
        files = results.get('files', [])

        # 復習スケジュールの判定（今日、1、3、7、30日前）
        today = datetime.datetime.now().date()
        targets = []
        for f in files:
            c_date = datetime.datetime.strptime(f['createdTime'][:10], '%Y-%m-%d').date()
            diff = (today - c_date).days
            if diff in [0, 1, 3, 7, 30]:
                targets.append(f)

        if not targets:
            st.success("🎉 本日の復習対象はありません。")
            st.balloons()
        else:
            st.info(f"📝 今日は {len(targets)} 件の復習があります。")
            
            for f in targets:
                st.subheader(f"問題: {f['name']}")
                # Googleドライブの画像を直接表示
                img_url = f"https://drive.google.com/uc?id={f['id']}"
                st.image(img_url, use_container_width=True)
                
                # AIにクイズを生成させるボタン
                if st.button(f"この画像からクイズを生成", key=f['id']):
                    with st.spinner("AIが問題を考えています..."):
                        # ここでAIが画像を分析して問題を出すロジック（簡略化）
                        st.write("💡 【AI解説】この画像の内容に基づいた重要ポイントを復習しましょう。")
                        # 実際の画像解析を入れる場合はここに model.generate_content を追記

    except Exception as e:
        # エラーが出た場合、具体的な原因を表示する
        st.error(f"⚠️ エラーが発生しました。設定を確認してください。\n\n詳細: {str(e)}")

if __name__ == "__main__":
    main()
