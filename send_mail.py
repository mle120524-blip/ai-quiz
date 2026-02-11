import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def get_targets():
    creds = Credentials.from_authorized_user_info({
        "token": os.environ["GOOGLE_TOKEN"],
        "refresh_token": os.environ["GOOGLE_REFRESH_TOKEN"],
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
    })
    service = build('drive', 'v3', credentials=creds)
    
    # 復習対象の日付リスト作成
    now = datetime.now()
    intervals = [1, 3, 7, 30]
    target_dates = [(now - timedelta(days=i)).strftime('%Y-%m-%d') for i in intervals]
    
    results = service.files().list(
        q=f"'{os.environ['DRIVE_FOLDER_ID']}' in parents",
        fields="files(id, name, createdTime)").execute()
    
    # 対象画像があるか判定
    found = [f for f in results.get('files', []) if f['createdTime'][:10] in target_dates]
    return len(found)

def send_email(count):
    msg = MIMEText(f"おはようございます！\n今日は復習対象の画像が {count} 枚あります。\n\nアプリを開く: https://ai-quiz-study.streamlit.app")
    msg['Subject'] = f"【行政書士AI】本日の復習（{count}件）"
    msg['From'] = os.environ['GMAIL_ADDRESS']
    msg['To'] = os.environ['GMAIL_ADDRESS']

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(os.environ['GMAIL_ADDRESS'], os.environ['GMAIL_APP_PASSWORD'])
        smtp.send_message(msg)

if __name__ == "__main__":
    count = get_targets()
    if count > 0:
        send_email(count)
    else:
        print("対象なし。メール送信をスキップします。")
