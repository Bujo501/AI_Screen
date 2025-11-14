from google_auth_oauthlib.flow import InstalledAppFlow
import os

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

CRED_PATH = "D:/S2_REC/credentials/gmail_credentials.json"
TOKEN_PATH = "D:/S2_REC/credentials/token.json"

def create_token():
    flow = InstalledAppFlow.from_client_secrets_file(CRED_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_PATH, "w") as token:
        token.write(creds.to_json())

    print("token.json created at:", TOKEN_PATH)

if __name__ == "__main__":
    create_token()
