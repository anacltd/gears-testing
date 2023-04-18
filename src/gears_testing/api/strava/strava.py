import json
import logging
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from gears_testing.api.strava.authenticate_flow import InstalledAppFlow
from gears_testing.api.strava.utils import _request

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)

TOKEN_PATH = os.path.join(Path(__file__).parent, "token.json")
CRED_PATH = os.path.join(Path(__file__).parent, "credentials.json")
NOW_UNIX = int(datetime.now().strftime("%s"))


class StravaAPI:
    base_url = "https://www.strava.com/api/v3/"

    def __init__(self):
        self._session = requests.Session()
        retries = Retry(total=5, backoff_factor=.5, status_forcelist=[502, 503, 504])
        self._session.mount('http://', HTTPAdapter(max_retries=retries))
        self._session.mount('https://', HTTPAdapter(max_retries=retries))

    def strava_api_connection(self):
        creds = None
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, "r") as json_file:
                creds = json.load(json_file)
                if creds['expires_at'] < NOW_UNIX:
                    creds = None
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(CRED_PATH, "activity:read_all,profile:read_all")
            creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, 'w') as token:
                token.write(json.dumps(creds))
        self._session.headers.update({"Authorization": f"Bearer {creds['access_token']}"})

    def get_athlete_activities(self, **kwargs):
        self.strava_api_connection()
        target_url = urljoin(self.base_url, 'athlete/activities')
        return _request(self._session, "GET", target_url, params=kwargs)
