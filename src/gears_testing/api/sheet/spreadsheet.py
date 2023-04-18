from __future__ import print_function

import logging
import os.path
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logging.basicConfig(filename=f'/tmp/{datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")}.log',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)
TOKEN_PATH = os.path.join(Path(__file__).parent, "token.json")
CRED_PATH = os.path.join(Path(__file__).parent, "credentials.json")


class GoogleSheetAPI(object):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def google_sheet_api_connection(self):
        """ Create a connection with the Google Sheet API """
        creds = None
        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, self.SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CRED_PATH, self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
        return build('sheets', 'v4', credentials=creds, cache_discovery=False)

    def upload_data(self, spreadsheet_id: str, data_to_upload: list, rg: str = None):
        try:
            service = self.google_sheet_api_connection()
            service.spreadsheets().values().update(spreadsheetId=spreadsheet_id,
                                                   range=rg or "A2:I",
                                                   valueInputOption='USER_ENTERED',
                                                   body={'values': data_to_upload}).execute()
            logger.info('DATA UPLOADED SUCCESSFULLY')
        except Exception as e:
            logger.error(e)

    def retrieve_data_from_google_sheet(self, spreadsheet_id: str, rg: str = None):
        """
        Retrieve data from a Google spreadsheet and load it into a Dataframe object
        :param spreadsheet_id:
        :param rg:
        :return: a Dataframe (empty if not data was found)
        """
        service = self.google_sheet_api_connection()
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=rg or "A2:I").execute()
        values = result.get('values', [])
        return values
