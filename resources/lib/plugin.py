import arrow

from matthuisman import plugin, gui, settings, userdata, signals, inputstream
from matthuisman.exceptions import PluginError

from .api import API
from .language import _
from .constants import WV_LICENSE_URL

api = API()

@signals.on(signals.BEFORE_DISPATCH)
def before_dispatch():
    api.new_session()
    plugin.logged_in = api.logged_in

@plugin.route('')
def home(**kwargs):
    folder = plugin.Folder()

    if not api.logged_in:
        folder.add_item(label=_(_.LOGIN, _bold=True), path=plugin.url_for(login))
    else:
        folder.add_item(label=_(_.LIVE_CHANNELS, _bold=True), path=plugin.url_for(live_channels))

        folder.add_item(label=_(_.CATCH_UP, _bold=True), path=plugin.url_for(catch_up))
        folder.add_item(label=_(_.MATCH_HIGHLIGHTS, _bold=True), path=plugin.url_for(catch_up, catalog_id='Match_Highlights', title=_.MATCH_HIGHLIGHTS))
        folder.add_item(label=_(_.INTERVIEWS, _bold=True), path=plugin.url_for(catch_up, catalog_id='Interviews', title=_.INTERVIEWS))
        folder.add_item(label=_(_.SPECIALS, _bold=True), path=plugin.url_for(catch_up, catalog_id='Specials', title=_.SPECIALS))

    folder.add_item(label=_.SETTINGS, path=plugin.url_for(plugin.ROUTE_SETTINGS))

    return folder

@plugin.route()
def live_channels(**kwargs):
    folder = plugin.Folder(title=_.LIVE_CHANNELS)

    for row in api.live_channels():
        folder.add_item(
            label = row['Name'],
            art   = {'thumb': row['Logo'].replace('_114X66', '')},
            info  = {'plot': row.get('Description')},
            path  = plugin.url_for(play, channel_id=row['Id'], is_live=True),
            playable = True,
        )

    return folder

@plugin.route()
def catch_up(catalog_id='', title=_.CATCH_UP, **kwargs):
    folder = plugin.Folder(title=title)

    for row in api.catch_up(catalog_id=catalog_id):
        folder.add_item(
            label = row['Name'],
            art   = {'thumb': row.get('Headline')},
            info  = {'plot': row.get('Description')},
            path  = plugin.url_for(play, vod_id=row['Id'], is_live=True),
            playable = True,
        )

    return folder

@plugin.route()
def login(**kwargs):
    username = gui.input(_.ASK_USERNAME, default=userdata.get('username', '')).strip()
    if not username:
        return

    userdata.set('username', username)

    password = gui.input(_.ASK_PASSWORD, hide_input=True).strip()
    if not password:
        return

    api.login(username=username, password=password)
    gui.refresh()

@plugin.route()
@plugin.login_required()
def play(channel_id=None, vod_id=None, **kwargs):
    asset = api.play(channel_id, vod_id)

    mpd_url = '{}?{}'.format(asset['Path'], asset['CdnTicket'])

    headers = {
        'Authorization':   asset['DrmToken'],
        'X-CB-Ticket':     asset['DrmTicket'],
        'X-ErDRM-Message': asset['DrmTicket'],
    }

    return plugin.Item(
        path = mpd_url,
        inputstream = inputstream.Widevine(license_key=WV_LICENSE_URL),
        headers = headers,
    )

@plugin.route()
def logout(**kwargs):
    if not gui.yes_no(_.LOGOUT_YES_NO):
        return

    api.logout()
    gui.refresh()

@plugin.login_required()
def epg():
    epg_data = []

    for row in api.epg():
        channel = {
            'id': row['ChannelId'],
            'display-name': row['ChannelName'],
            'icon': row['ChannelLogo'].replace('_114X66', ''),
            'programs': [],
        }

        for row2 in row['Programs']:
            channel['programs'].append({
                'start': int(arrow.get(row2['StartTime']).to('utc').format('X')),
                'stop': int(arrow.get(row2['EndTime']).to('utc').format('X')),
                'title': row2['Name'],
                'desc': row2['Description'],
              #  'sub-title': row2['Description'],
            })

        epg_data.append(channel)

    return epg_data

@plugin.login_required()
def playlist():
    playlist_data = []

    for row in api.live_channels():
        channel = {
            'id': row['Id'],
            'display-name': row['Name'],
            'icon': row['Logo'].replace('_114X66', ''),
            'url': plugin.url_for(play, channel_id=row['Id']),
        }

        playlist_data.append(channel)

    return playlist_data