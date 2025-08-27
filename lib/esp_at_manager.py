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

        if not self.restart(5000):
            raise Exception("module restart failed.")

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
            if not find_util(self._stream, "\r\nOK\r\n", 1000):
                raise Exception("AT command failed.")

    @property
    def wifi(self):
        return self._wifi

    @property
    def mqtt(self):
        return self._mqtt

    def restart(self, timeout_ms: int):
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
            self._stream.write("AT+RST\r\n")
            if find_util(self._stream, "\r\nOK\r\n", 100) and find_util(
                self._stream, "\r\nready\r\n", 2000
            ):
                self._stream.write("AT\r\n")
                if find_util(self._stream, "\r\nOK\r\n", 100):
                    return True
            else:
                self.cancel_send()

        return False

    def cancel_send(self):
        time.sleep_ms(30)
        self._stream.write("+++")
        if find_util(self._stream, "\r\nSEND Canceled\r\n", 100):
            self._stream.write("\r\n")
            empty_rx(self._stream, 100)
            return False
        return True