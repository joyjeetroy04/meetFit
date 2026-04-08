import os
import shutil
import time
from datetime import datetime

# Google API Imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.json.
# This scope only allows the app to see/edit files IT created.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class CloudEngine:
    def __init__(self, data_dir="data", backup_dir="cloud_backups"):
        self.data_dir = data_dir
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)

    def get_local_size_mb(self):
        if not os.path.exists(self.data_dir):
            return 0.0
            
        total_size = 0
        for dirpath, _, filenames in os.walk(self.data_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return round(total_size / (1024 * 1024), 2)

    def package_brain_for_cloud(self):
        print("[Cloud Engine] Packaging local brain...")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"OS_Brain_Backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)

        shutil.make_archive(backup_path, 'zip', self.data_dir)
        final_file = f"{backup_path}.zip"
        
        return final_file

    def upload_to_drive(self, file_path):
        """Authenticates with Google and uploads the zip file to Drive."""
        print("[Cloud Engine] Initiating Google Drive handshake...")
        creds = None
        
        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    raise Exception("Missing credentials.json! Please download it from Google Cloud Console.")
                
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            # Build the Drive API service
            service = build('drive', 'v3', credentials=creds)

            file_metadata = {'name': os.path.basename(file_path)}
            media = MediaFileUpload(file_path, mimetype='application/zip', resumable=True)
            
            print(f"[Cloud Engine] Uploading {os.path.basename(file_path)} to Drive...")
            
            # Execute the upload
            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            
            print(f"[Cloud Engine] Upload successful! File ID: {file.get('id')}")
            return True

        except Exception as error:
            print(f"[Cloud Engine] An error occurred during upload: {error}")
            raise error