from esp_at_stream_util import *

__version__ = "1.0.0"


class EspAtWifi:
    def __init__(self, stream):
        self._stream = stream

    def connect_wifi(self, ssid: str, password: str, timeout_ms: int):
        if not ssid or password is None or timeout_ms < 0:
            raise ValueError("connect wifi,invalid parameters.")

        command = 'AT+CWJAP="{}","{}"'.format(ssid, password)
        targets = (
            "\r\nOK\r\n",
            "\r\nERROR\r\n",
            "busy p...\r\n",
        )
        self._stream.write(command + "\r\n")
        return find_util(self._stream, targets, timeout_ms) == 0

    def get_ip_info(self):
        self._stream.write("AT+CIPSTA?\r\n")
        if find_util(self._stream, '+CIPSTA:ip:"', 500) != 0:
            return (None, None, None)

        ip = read_until(self._stream, '"', 500)

        gateway = None
        if find_util(self._stream, '+CIPSTA:gateway:"', 100) == 0:
            gateway = read_until(self._stream, '"', 500)

        netmask = None
        if find_util(self._stream, '+CIPSTA:netmask:"', 100) == 0:
            netmask = read_until(self._stream, '"', 500)

        if find_util(self._stream, "\r\nOK\r\n", 100) == 0:
            return (ip, gateway, netmask)

        return (None, None, None)

    def get_mac(self):
        self._stream.write("AT+CIPSTAMAC?\r\n")
        if find_util(self._stream, '+CIPSTAMAC:"', 500) != 0:
            return None

        mac = read_until(self._stream, '"', 500)
        if find_util(self._stream, "\r\nOK\r\n", 100) == 0:
            return mac

        return None

    def get_ap_info(self):
        self._stream.write("AT+CWJAP?\r\n")
        if find_util(self._stream, '+CWJAP:"', 500) != 0:
            return (None, None, None, None)

        ssid = read_until(self._stream, '"', 500)
        if not skip_next(self._stream, ",", 500) or not skip_next(
            self._stream, '"', 500
        ):
            return (None, None, None, None)

        bssid = read_until(self._stream, '"', 500)
        if not skip_next(self._stream, ",", 500):
            return (None, None, None, None)

        channel = parse_int(self._stream, 500)
        rssi = parse_int(self._stream, 500)

        if find_util(self._stream, "\r\nOK\r\n", 100) == 0:
            return (ssid, bssid, channel, rssi)
        return (None, None, None, None)
