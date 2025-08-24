from esp_at_stream_util import *
from esp_at_result_code import ResultCode
from esp_at_wifi import EspAtWifi
from esp_at_mqtt import EspAtMqtt
import time

__version__ = "1.0.0"


class EspAtManager:
    def __init__(self, stream):
        self._stream = stream
        self._wifi = EspAtWifi(stream)
        self._mqtt = EspAtMqtt(stream)
        
        restart_result = self.restart()
        
        if restart_result != ResultCode.OK:
            raise Exception("module restart failed: {}".format(ResultCode.to_string(restart_result)))
        
        at_commands = (
            "ATE0",
            "AT+CWINIT=1",
            "AT+CWMODE=1",
            "AT+CIPDINFO=1",
            "AT+CWAUTOCONN=0",
            "AT+CWDHCP=1,1",
        )
        
        targets = ("\r\nOK\r\n", "\r\nERROR\r\n", "busy p...\r\n",)
        timeout = 1000
        
        for command in at_commands:
            self._stream.write(command + "\r\n")
            index = find_util(self._stream, targets, timeout)
            if index != 0:
                raise Exception("AT command failed: {}, response index: {}".format(command, index))

    @property
    def wifi(self):
        return self._wifi

    @property
    def mqtt(self):
        return self._mqtt
    
    def restart(self):
        start_time = time.ticks_ms()

        while time.ticks_diff(time.ticks_ms(), start_time) < 5000:
            self._stream.write("AT+RST\r\n")
            if (
                find_util(self._stream, ("\r\nOK\r\n",), 100) == 0
                and find_util(self._stream, ("\r\nready\r\n",), 2000) == 0
            ):
                self._stream.write("AT\r\n")
                if find_util(self._stream, ("\r\nOK\r\n",), 100) == 0:
                    return ResultCode.OK
            else:
                self.cancel_send()

        return ResultCode.ERROR

    def cancel_send(self):
        time.sleep_ms(30)
        self._stream.write("+++")

        if find_util(self._stream, ("\r\nSEND Canceled\r\n",), 100) == 0:
            self._stream.write("\r\n")
            empty_rx(self._stream, 100)
            return False
        return True
