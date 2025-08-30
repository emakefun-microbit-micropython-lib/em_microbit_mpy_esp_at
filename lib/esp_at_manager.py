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
            if find_util(self._stream, targets, 500) != 0:
                raise Exception("AT command failed.")

    @property
    def wifi(self):
        return self._wifi

    @property
    def mqtt(self):
        return self._mqtt

    def restart(self, timeout_ms: int):
        if timeout_ms < 0:
            raise ValueError("esp at restart,invalid timeout_ms parameter.")
        targets = (
            "\r\nOK\r\n",
            "\r\nERROR\r\n",
            "busy p...\r\n",
        )
        start_time = time.ticks_ms()
        while True:
            self._stream.write("AT+RST\r\n")
            if (
                find_util(self._stream, targets, 100) == 0
                and find_util(self._stream, "\r\nready\r\n", 1000) == 0
            ):
                self._stream.write("AT\r\n")
                return find_util(self._stream, targets, 100) == 0
            else:
                self.cancel_send()
            if time.ticks_diff(time.ticks_ms(), start_time) >= timeout_ms:
                return False

    def cancel_send(self):
        time.sleep_ms(30)
        self._stream.write("+++")
        if find_util(self._stream, "\r\nSEND Canceled\r\n", 100) == 0:
            self._stream.write("\r\n")
            while self._stream.any():
                self._stream.read()
            return False
        return True
