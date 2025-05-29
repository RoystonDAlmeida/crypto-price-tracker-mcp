"""
Google Sheets client for exporting cryptocurrency data
"""
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleSheetsClient:
    """
    Google Sheets client for handling spreadsheet data
    """
    
    def __init__(self, credentials_file: str = None):
        """
        Initialize the Google Sheets client
        
        Args:
            credentials_file: Path to Google service account credentials JSON file
        """

        self.service = None
        self.active_spreadsheet_id = None
        self.active_spreadsheet_name = None
        self.credentials_file = credentials_file
        self.drive_service = None # For finding files by name
        
        # Define the scope for Google Sheets API
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]
        
        # Initialize the service if credentials are provided
        if credentials_file and os.path.exists(credentials_file):
            self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Sheets and Drive services with credentials"""
        
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=self.scopes
            )

            self.service = build('sheets', 'v4', credentials=credentials)
            self.drive_service = build('drive', 'v3', credentials=credentials)
            
            print("Google Sheets and Drive services initialized successfully.")
            return True
        
        except Exception as e:
            print(f"Error initializing Google services: {e}")

            self.service = None
            self.drive_service = None
            return False

    
    def create_spreadsheet(self, title: str) -> Optional[str]:
        """
        Create a new Google Spreadsheet
        
        Args:
            title: Title of the new spreadsheet
            
        Returns:
            Spreadsheet ID if successful, None otherwise
        """

        if not self.service:
            print("Google Sheets service not initialized. Cannot create spreadsheet.")
            return None
            
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                }
            }
            
            result = self.service.spreadsheets().create(body=spreadsheet).execute()
            spreadsheet_id = result.get('spreadsheetId')
            
            self.active_spreadsheet_id = spreadsheet_id
            self.active_spreadsheet_name = title
            
            print(f"Created spreadsheet: {title} (ID: {spreadsheet_id})")
            return spreadsheet_id
            
        except HttpError as e:
            print(f"Error creating spreadsheet: {e}")
            return None
    
    def get_or_create_spreadsheet(self, title: str) -> Optional[str]:
        """
        Get existing spreadsheet or create new one
        
        Args:
            title: Title of the spreadsheet
            
        Returns:
            Spreadsheet ID if successful, None otherwise
        """

        if not self.drive_service:
            print("Google Drive service not initialized. Cannot search for spreadsheet.")
            # Fallback to trying to create, though it might also fail if sheets service is down
            return self.create_spreadsheet(title)

        try:
            # Search for existing spreadsheet by title
            query = f"mimeType='application/vnd.google-apps.spreadsheet' and name='{title}' and trashed=false"
            response = self.drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            files = response.get('files', [])
            
            if files:
                spreadsheet_id = files[0]['id']
                self.active_spreadsheet_id = spreadsheet_id
                self.active_spreadsheet_name = files[0]['name'] # Use actual name from Drive
                print(f"Found existing spreadsheet: '{self.active_spreadsheet_name}' (ID: {spreadsheet_id})")
                return spreadsheet_id
            else:
                print(f"Spreadsheet '{title}' not found. Creating a new one.")
                return self.create_spreadsheet(title)
        except HttpError as e:
            print(f"Error searching for spreadsheet '{title}': {e}")
            return None
    
    def export_data(self, sheet_name: str, data: List[Dict[str, Any]], user_email_to_share: Optional[str] = None) -> bool:
        """
        Export data to Google Sheets
        
        Args:
            sheet_name: Name of the sheet/spreadsheet
            data: List of dictionaries with data to export
            user_email_to_share: Optional email address to share the created sheet with.
            
        Returns:
            True if export was successful, False otherwise
        """

        if not self.service:
            print("Google Sheets service not initialized")
            return False
        
        if not data:
            print("No data to export")
            return False
        
        try:
            # Create or get spreadsheet
            spreadsheet_id = self.get_or_create_spreadsheet(sheet_name)
            if not spreadsheet_id:
                return False
            
            # If a user email is provided and the sheet was successfully created, share it.
            # self.active_spreadsheet_id is set by get_or_create_spreadsheet -> create_spreadsheet
            if user_email_to_share and self.active_spreadsheet_id:
                print(f"Attempting to share spreadsheet '{self.active_spreadsheet_name}' (ID: {self.active_spreadsheet_id}) with {user_email_to_share}")
                shared_successfully = self.share_spreadsheet(email=user_email_to_share, role='writer')
                if shared_successfully:
                    print(f"Spreadsheet shared successfully with {user_email_to_share}.")
                else:
                    print(f"Failed to share spreadsheet with {user_email_to_share}. User may still need to request access manually or check service account permissions for Drive API.")
            
            # Convert data to DataFrame and add timestamp
            df = pd.DataFrame(data)
            df['Export_Time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Prepare data for Google Sheets (header + rows)
            headers = list(df.columns)
            rows = df.values.tolist()
            
            # Combine headers and data
            sheet_data = [headers] + rows
            
            # Clear existing data and write new data
            range_name = 'Sheet1!A1'
            
            # Clear the sheet first
            clear_request = {
                'ranges': ['Sheet1']
            }
            self.service.spreadsheets().values().batchClear(
                spreadsheetId=spreadsheet_id, 
                body=clear_request
            ).execute()
            
            # Write new data
            value_input_option = 'RAW'
            body = {
                'values': sheet_data
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()
            
            print(f"Successfully exported {len(data)} rows to Google Sheets. Applying formatting...")

            # Apply formatting
            # Assuming the data is always written to 'Sheet1', which typically has sheetId 0
            # For a more robust solution, you might fetch the sheetId dynamically.
            sheet_id = 0 # Default sheetId for the first sheet
            
            formatting_requests = []

            # 1. Bold headers
            formatting_requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0, # Header row
                        "endRowIndex": 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {"bold": True}
                        }
                    },
                    "fields": "userEnteredFormat.textFormat.bold"
                }
            })

            # Find column indices for specific formatting
            price_col_index = -1
            change_24h_col_index = -1
            try:
                if 'Price' in headers:
                    price_col_index = headers.index('Price')
                if 'Change_24h' in headers:
                    change_24h_col_index = headers.index('Change_24h')
            except ValueError:
                print("Warning: Could not find 'Price' or 'Change_24h' column for specific formatting.")

            # 2. Currency format for 'Price' column
            if price_col_index != -1:
                formatting_requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 1, # Data rows
                            "startColumnIndex": price_col_index,
                            "endColumnIndex": price_col_index + 1
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}
                            }
                        },
                        "fields": "userEnteredFormat.numberFormat"
                    }
                })

            # 3. Number format and Conditional formatting for 'Change_24h' column
            if change_24h_col_index != -1:
                # Number format (e.g., -0.27%)
                formatting_requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 1, # Data rows
                            "startColumnIndex": change_24h_col_index,
                            "endColumnIndex": change_24h_col_index + 1
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "numberFormat": {"type": "NUMBER", "pattern": "0.00\"%\""}
                            }
                        },
                        "fields": "userEnteredFormat.numberFormat"
                    }
                })
                # Conditional formatting for positive values (green text)
                formatting_requests.append({
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": change_24h_col_index, "endColumnIndex": change_24h_col_index + 1}],
                            "booleanRule": {
                                "condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "0"}]},
                                "format": {"textFormat": {"foregroundColor": {"red": 0.0, "green": 0.6, "blue": 0.0}}} # Dark Green
                            }
                        }, "index": 0
                    }
                })
                # Conditional formatting for negative values (red text)
                formatting_requests.append({
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": change_24h_col_index, "endColumnIndex": change_24h_col_index + 1}],
                            "booleanRule": {
                                "condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "0"}]},
                                "format": {"textFormat": {"foregroundColor": {"red": 0.8, "green": 0.0, "blue": 0.0}}} # Dark Red
                            }
                        }, "index": 1
                    }
                })

            if formatting_requests:
                try:
                    self.service.spreadsheets().batchUpdate(
                        spreadsheetId=spreadsheet_id,
                        body={"requests": formatting_requests}
                    ).execute()
                    print("Successfully applied formatting to the sheet.")
                except HttpError as e:
                    print(f"Error applying formatting: {e}")
            
            return True
            
        except HttpError as e:
            print(f"Google Sheets API error: {e}")
            return False
        
        except Exception as e:
            print(f"Error exporting data to Google Sheets: {e}")
            return False
    
    def share_spreadsheet(self, email: str, role: str = 'writer') -> bool:
        """
        Share the active spreadsheet with an email address
        
        Args:
            email: Email address to share with
            role: Permission level ('reader', 'writer', 'owner')
            
        Returns:
            True if sharing was successful, False otherwise
        """

        if not self.drive_service or not self.active_spreadsheet_id:
            print("Drive service not initialized or no active spreadsheet to share.")
            return False
        
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            
            self.drive_service.permissions().create( # Use self.drive_service
                fileId=self.active_spreadsheet_id,
                body=permission,
                sendNotificationEmail=True
            ).execute()
            
            # Message is now printed in export_data for context
            return True
        
        except HttpError as e:
            if e.resp.status == 403:
                 print(f"Error sharing spreadsheet: Insufficient permissions for the service account to share files. Details: {e}")
            elif e.resp.status == 400 and "invalidSharingRequest" in str(e.content): # type: ignore
                 print(f"Error sharing spreadsheet: Invalid sharing request, possibly due to an invalid email address '{email}'. Details: {e}")
            else:
                print(f"Error sharing spreadsheet (HttpError): {e}")
            return False
        
        except Exception as e:
            print(f"Error sharing spreadsheet: {e}")
            return False
    
    def get_spreadsheet_url(self) -> Optional[str]:
        """
        Get the URL of the active spreadsheet
        
        Returns:
            URL string if available, None otherwise
        """

        if self.active_spreadsheet_id:
            return f"https://docs.google.com/spreadsheets/d/{self.active_spreadsheet_id}/edit"
        return None
    
    async def close(self):
        """Close the client connection"""

        # No explicit cleanup needed for Google API client
        pass