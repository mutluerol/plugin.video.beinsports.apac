from resources.lib import plugin
from resources.lib.matthuisman import signals

signals.emit(signals.BEFORE_DISPATCH)

def playlist():
    return plugin.playlist()

def epg():
    return plugin.epg()