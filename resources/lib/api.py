import json
import re
import math
import arrow

from matthuisman import userdata, settings
from matthuisman.session import Session
from matthuisman.exceptions import Error

from .constants import HEADERS, API_BASE, TOKEN_COOKIE_KEY, PAGESIZE
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
            "BuildNo": "121",
            "ClientVersion": "1.2.5",
            #"ConnectionType": "WIFI",
            #"Country": "5244",
            #"CpuAbi": "arm64-v8a",
            #"CpuAbi2": "armeabi-v7a",
            #"DeviceBrand": "",
            #"DeviceFirmwareVersion": "",
            #"DeviceHardware": "",
            #"DeviceHardwareVersion": "",
            #"DeviceId": "4572df18da524542",
            "DeviceManufacturer": "",
            "DeviceModel": "",
            "DeviceName": "AndroidPhone",
            #"DeviceOsVersion": "",
            #"DeviceType": "",
            "IsRoot": "false",
            "Language": "EN",
            #"OsArch": "",
            #"ScreenSize": "",
        }

        data = self._session.post('/api/init', json=payload).json()
        #access_token = data['AccessToken']

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

    def epg(self, start=None, end=None):
        start = start or arrow.utcnow()
        end   = end or start.shift(days=7)

        payload = {
            'StartTime': start.format('YYYY-MM-DDTHH:mm:00.000') + 'Z',
            'EndTime':   end.format('YYYY-MM-DDTHH:mm:00.000') + 'Z',
            'OnlyLiveEvents': 'false',
        }

        return self._session.post('/api/tvguide', json=payload).json()['List']

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

        return data['List'][0]

    def logout(self):
        userdata.delete('token')
        self.new_session()