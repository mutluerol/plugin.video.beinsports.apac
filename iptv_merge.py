from resources.lib import plugin

plugin.before_dispatch()

def playlist():
    return plugin.playlist()

def epg():
    return plugin.epg()