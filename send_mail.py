import base64
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# load credentials
creds = Credentials.from_authorized_user_file('token.json', SCOPES)

# create service
service = build('gmail', 'v1', credentials=creds)

# create message
message = MIMEText("Hello from AI agent")
message['to'] = "sivasankarcsemit@gmail.com"
message['subject'] = "Test reply"

raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

# send message
service.users().messages().send(
    userId="me",
    body={'raw': raw}
).execute()

print("Mail sent successfully 🚀")