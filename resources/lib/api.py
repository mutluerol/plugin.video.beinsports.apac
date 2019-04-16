import json
import re
import math

from matthuisman import userdata, settings
from matthuisman.session import Session
from matthuisman.exceptions import Error

from .constants import HEADERS, API_BASE, TOKEN_COOKIE_KEY, WV_LICENSE_URL, PAGESIZE
from .language import _

class APIError(Error):
    pass

class API(object):
    def new_session(self):
        self.logged_in = False

        self._session = Session(HEADERS, base_url=API_BASE)
        self._set_authentication()

    def _set_authentication(self):
        token = userdata.get('token')
        if not token:
            settings.setBool('_logged_in', False)
            return

        self._session.cookies.update({TOKEN_COOKIE_KEY: token})
        self.logged_in = True

        settings.setBool('_logged_in', True)

    def login(self, username, password):
        self.logout()

        payload = {
            'ClientVersion': '1.2.5',
            'DeviceName': 'AndroidPhone',
            #'DeviceId': 'af62e6edf7dd3661',
        }

        data = self._session.post('/api/init', json=payload).json()
        access_token = data['AccessToken']

        payload = {
            #'Action' : '/View/Account/SubmitLogin',
            'jsonModel': json.dumps({
                'Username': username,
                'Password': password,
            }),
            'captcha': '',
        }

        page  = self._session.post(data['SubmitLoginLink'], json=payload).text

        if 'authorize?token' not in page:
            raise APIError(_.LOGIN_ERROR)

        token = self._session.cookies[TOKEN_COOKIE_KEY]

        userdata.set('token', token)
        self._set_authentication()

    def live_channels(self):
        items = []

        for i in range(10):
            payload = {
                'Page': i,
                'PageSize': PAGESIZE,
            }

            data = self._session.post('/api/livesports', json=payload).json()
            items.extend(data['Channels'])

            if len(data['Channels']) < PAGESIZE:
                break

        return items

    def catch_up(self, catalog_id=''):
        items = []

        for i in range(10):
            payload = {
                'Page': i,
                'PageSize': PAGESIZE,
                'Type': 'CATCH_UP',
                'CatalogId': catalog_id,
            }

            data = self._session.post('/api/catchups', json=payload).json()
            items.extend(data['List'])

            if len(data['List']) < PAGESIZE:
                break

        return items

    def play(self, channel_id=None, vod_id=None):
        payload = {
            'ChannelId': channel_id,
            'VodId': vod_id,
        }

        data = self._session.post('/api/play', json=payload).json()

        if 'List' not in data:
            raise APIError(_.NO_STREAM)

        selected = data['List'][0]
        mpd_url =  '{}?{}'.format(selected['Path'], selected['CdnTicket'])

        license_headers = {
            'Authorization': selected['DrmToken'],
            'X-CB-Ticket': selected['DrmTicket'],
            'X-ErDRM-Message': selected['DrmTicket'],
        }

        return mpd_url, WV_LICENSE_URL, license_headers

    def logout(self):
        userdata.delete('token')
        self.new_session()