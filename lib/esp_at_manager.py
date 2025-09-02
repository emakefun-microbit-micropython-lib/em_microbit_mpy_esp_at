from esp_at_stream_util import *
from esp_at_wifi import EspAtWifi
from esp_at_mqtt import EspAtMqtt
import time

__version__ = "1.0.0"


class EspAtManager:
    def __init__(self, stream):
        self._stream = stream
        self._wifi = EspAtWifi(stream)
        self._mqtt = EspAtMqtt(stream)

        if not self.restart(2000):
            raise Exception("module restart failed.")

        at_commands = (
            "ATE0",
            "AT+CWINIT=1",
            "AT+CWMODE=1",
            "AT+CIPDINFO=1",
            "AT+CWAUTOCONN=0",
            "AT+CWDHCP=1,1",
        )
        targets = (
            "\r\nOK\r\n",
            "\r\nERROR\r\n",
            "busy p...\r\n",
        )
        for command in at_commands:
            self._stream.write(command + "\r\n")
            if multi_find_util(self._stream, targets, 500) != 0:
                raise Exception("esp at init failed.")

    @property
    def wifi(self):
        return self._wifi

    @property
    def mqtt(self):
        return self._mqtt

    def restart(self, timeout_ms: int):
        if timeout_ms < 0:
            raise ValueError("Error: 'restart' function, invalid parameter.")
        targets = (
            "\r\nOK\r\n",
            "\r\nERROR\r\n",
            "busy p...\r\n",
        )
        end_time = time.ticks_add(time.ticks_ms(), timeout_ms)
        while True:
            self._stream.write("AT+RST\r\n")
            if multi_find_util(self._stream, targets, 100) == 0 and single_find_util(
                self._stream, "\r\nready\r\n", 1000
            ):
                self._stream.write("AT\r\n")
                return multi_find_util(self._stream, targets, 100) == 0
            else:
                self.cancel_send()
            if time.ticks_diff(time.ticks_ms(), end_time) >= 0:
                return False

    def cancel_send(self):
        time.sleep_ms(30)
        self._stream.write("+++")
        if single_find_util(self._stream, "\r\nSEND Canceled\r\n", 100):
            self._stream.write("\r\n")
            self._stream.read()
            return False
        return True
