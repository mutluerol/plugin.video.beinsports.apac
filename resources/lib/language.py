from matthuisman.language import BaseLanguage

class Language(BaseLanguage):
    ASK_USERNAME     = 30001
    ASK_PASSWORD     = 30002
    LOGIN_ERROR      = 30003
    NO_STREAM        = 30004
    LIVE_CHANNELS    = 30005
    CATCH_UP         = 30006
    MATCH_HIGHLIGHTS = 30007
    INTERVIEWS       = 30008
    SPECIALS         = 30009
    
_ = Language()