##
# Informations for calls, state and language
##
from enum import Enum
import logging


class CallState(Enum):
    CALL_INIT = 1
    CALL_OBTAIN_LANGUAGE = 2
    CALL_GET_CONSENT = 3


class LanguageChoice(Enum):
    LANG_EN_US = 1
    LANG_EN_GB = 2
    LANG_CNM_CN = 3


class Call:
    def __init__(self, session_uuid, call_uuid, source, destination, host):
        self.session_uuid = session_uuid
        self.call_uuid = call_uuid
        self.source = source
        self.destination = destination
        self.state = CallState.CALL_INIT
        self.language = None
        self.host = host

    def next_state(self):
        val = self.state.value
        try:
            self.state = CallState(val + 1)
        except ValueError:
            logging.error('Call state is over.')

    def is_last_state(self):
        return self.state.value == len(list(CallState))

    def set_language(self, lang):
        self.language = lang
