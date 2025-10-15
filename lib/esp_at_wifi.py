from esp_at_stream_util import *


class EspAtWifi:
    def __init__(self, stream):
        self._stream = stream

    def connect_wifi(self, ssid: str, password: str):
        command = 'AT+CWJAP="{}","{}"'.format(ssid, password)
        targets = (
            "\r\nOK\r\n",
            "\r\nERROR\r\n",
            "busy p...\r\n",
        )
        self._stream.write(command + "\r\n")
        return multi_find_util(self._stream, targets, 15000) == 0
