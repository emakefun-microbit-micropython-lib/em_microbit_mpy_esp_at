from esp_at_stream_util import *
from esp_at_result_data import ResultData

__version__ = "1.0.0"


class EspAtWifi:
    def __init__(self, stream):
        self._stream = stream

    def connect_wifi(self, ssid: str, password: str, timeout_ms: int):
        if not ssid or password is None or timeout_ms <= 0:
            return False

        command = 'AT+CWJAP="{}","{}"'.format(ssid, password)
        self._stream.write(command + "\r\n")
        return find_util(self._stream, "\r\nOK\r\n", timeout_ms)

    def get_ip_info(self):

        self._stream.write("AT+CIPSTA?\r\n")
        if not find_util(self._stream, '+CIPSTA:ip:"', 1000):
            return ResultData(success=False)

        ip = read_until(self._stream, '"', 1000)

        gateway = None
        if find_util(self._stream, '+CIPSTA:gateway:"', 100):
            gateway = read_until(self._stream, '"', 1000)

        netmask = None
        if find_util(self._stream, '+CIPSTA:netmask:"', 100):
            netmask = read_until(self._stream, '"', 1000)

        if find_util(self._stream, "\r\nOK\r\n", 100):
            return ResultData(success=True, ip=ip, gateway=gateway, netmask=netmask)

        return ResultData(success=False)

    def get_mac(self):
        self._stream.write("AT+CIPSTAMAC?\r\n")
        if not find_util(self._stream, '+CIPSTAMAC:"', 1000):
            return ResultData(success=False)

        mac = read_until(self._stream, '"', 1000)
        if find_util(self._stream, "\r\nOK\r\n", 100):
            return ResultData(success=True, mac=mac)

        return ResultData(success=False)

    def get_ap_info(self):
        self._stream.write("AT+CWJAP?\r\n")
        if not find_util(self._stream, '+CWJAP:"', 1000):
            return ResultData(success=False)

        ssid = read_until(self._stream, '"', 1000)
        if not skip_next(self._stream, ",", 1000) or not skip_next(
            self._stream, '"', 1000
        ):
            return ResultData(success=False)

        bssid = read_until(self._stream, '"', 1000)
        if not skip_next(self._stream, ",", 1000):
            return ResultData(success=False)

        channel = parse_int(self._stream, 1000)
        rssi = parse_int(self._stream, 1000)

        if find_util(self._stream, "\r\nOK\r\n", 100):
            return ResultData(
                success=True, ssid=ssid, bssid=bssid, channel=channel, rssi=rssi
            )
        return ResultData(success=False)
