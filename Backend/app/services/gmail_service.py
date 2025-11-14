from email.mime.text import MIMEText
import base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import os

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

class GmailService:
    def __init__(self):
        self.creds = None
        self.token_path = "D:/S2_REC/Backend/credentials/token.json"
        self.cred_path = "D:/S2_REC/Backend/credentials/gmail_credentials.json"
        self.creds = self.get_credentials()

    def get_credentials(self):
        if os.path.exists(self.token_path):
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            return creds

        flow = InstalledAppFlow.from_client_secrets_file(self.cred_path, SCOPES)
        creds = flow.run_local_server(port=0)

        with open(self.token_path, "w") as token:
            token.write(creds.to_json())

        return creds

    def build_service(self):
        return build("gmail", "v1", credentials=self.creds)

    def send_email(self, to_email: str, subject: str, message_text: str):
        service = self.build_service()

        message = MIMEText(message_text)
        message["to"] = to_email
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        sent = service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        return {"message_id": sent["id"], "status": "Email sent successfully!"}
