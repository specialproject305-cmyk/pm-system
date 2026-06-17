import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import streamlit as st

# Konfigurasi
SERVICE_ACCOUNT_FILE = "service_account.json"  # Ganti dengan file service account
DRIVE_FOLDER_ID = "1soOsPCQ3yYF_9P-Yc8EIbdQRFvb61KQd"  # Ganti dengan Folder ID Google Drive

def upload_to_drive(file_path, file_name):
    """Upload file ke Google Drive"""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        
        service = build('drive', 'v3', credentials=credentials)
        
        file_metadata = {
            'name': file_name,
            'parents': [DRIVE_FOLDER_ID]
        }
        
        media = MediaFileUpload(file_path, mimetype='image/jpeg', resumable=True)
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        return {
            'file_id': file.get('id'),
            'url': file.get('webViewLink')
        }
    except Exception as e:
        st.error(f"Upload failed: {e}")
        return None
