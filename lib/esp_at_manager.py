from esp_at_stream_util import *
from esp_at_wifi import EspAtWifi
from esp_at_mqtt import EspAtMqtt
from microbit import panic
import time

COMMON_TARGETS = (
    "\r\nOK\r\n",
    "\r\nERROR\r\n",
    "busy p...\r\n",
)


class EspAtManager:
    def __init__(self, stream):
        self._stream = stream
        self._wifi = EspAtWifi(stream)
        self._mqtt = EspAtMqtt(stream)

        if not self.restart(2000):
            panic(9)

        at_commands = (
            "ATE0",
            "AT+CWINIT=1",
            "AT+CWMODE=1",
            "AT+CIPDINFO=1",
            "AT+CWAUTOCONN=0",
            "AT+CWDHCP=1,1",
        )
        for command in at_commands:
            self._stream.write(command + "\r\n")
            if multi_find_util(self._stream, COMMON_TARGETS, 500) != 0:
                panic(9)

    @property
    def wifi(self):
        return self._wifi

    @property
    def mqtt(self):
        return self._mqtt

    def restart(self, timeout_ms: int):
        end_time = time.ticks_add(time.ticks_ms(), timeout_ms)
        while True:
            self._stream.write("AT+RST\r\n")
            if (
                multi_find_util(self._stream, COMMON_TARGETS, 100) == 0
                and multi_find_util(self._stream, ("\r\nready\r\n",), 1000) == 0
            ):
                self._stream.write("AT\r\n")
                return multi_find_util(self._stream, COMMON_TARGETS, 100) == 0
            else:
                self.cancel_send()
            if time.ticks_diff(time.ticks_ms(), end_time) >= 0:
                return False

    def cancel_send(self):
        time.sleep_ms(30)
        self._stream.write("+++")
        if multi_find_util(self._stream, ("\r\nSEND Canceled\r\n",), 100) != 0:
            self._stream.write("\r\n")
            self._stream.read()
            return False
        return True
