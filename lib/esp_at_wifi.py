from esp_at_stream_util import *

__version__ = "1.0.0"


class EspAtWifi:
    def __init__(self, stream):
        self._stream = stream

    def connect_wifi(self, ssid: str, password: str):
        if not ssid or password is None:
            raise ValueError("connect wifi,invalid parameters.")
        command = 'AT+CWJAP="{}","{}"'.format(ssid, password)
        targets = (
            "\r\nOK\r\n",
            "\r\nERROR\r\n",
            "busy p...\r\n",
        )
        self._stream.write(command + "\r\n")
        return multi_find_util(self._stream, targets, 15000) == 0

    def get_ip_info(self):
        targets = (
            '+CIPSTA:ip:"',
            "\r\nERROR\r\n",
            "busy p...\r\n",
        )
        self._stream.write("AT+CIPSTA?\r\n")
        if multi_find_util(self._stream, targets, 500) != 0:
            return None

        ip = read_until(self._stream, '"', 500)
        gateway = None
        netmask = None

        if single_find_util(self._stream, '+CIPSTA:gateway:"', 100):
            gateway = read_until(self._stream, '"', 500)
        if single_find_util(self._stream, '+CIPSTA:netmask:"', 100):
            netmask = read_until(self._stream, '"', 500)
        if None in (ip, gateway, netmask):
            return None
        if single_find_util(self._stream, "\r\nOK\r\n", 100) == 0:
            return (ip, gateway, netmask)
        return None

    def get_mac(self):
        targets = (
            '+CIPSTAMAC:"',
            "\r\nERROR\r\n",
            "busy p...\r\n",
        )
        self._stream.write("AT+CIPSTAMAC?\r\n")
        if not multi_find_util(self._stream, targets, 500) != 0:
            return None
        mac = read_until(self._stream, '"', 500)
        if mac and single_find_util(self._stream, "\r\nOK\r\n", 100):
            return mac
        return None

    def get_ap_info(self):
        targets = (
            '+CWJAP:"',
            "\r\nERROR\r\n",
            "busy p...\r\n",
        )
        self._stream.write("AT+CWJAP?\r\n")
        if not multi_find_util(self._stream, targets, 500):
            return None
        ssid = read_until(self._stream, '"', 500)
        if (
            not ssid
            or not skip_next(self._stream, ",", 100)
            or not skip_next(self._stream, '"', 100)
        ):
            return None
        bssid = read_until(self._stream, '"', 500)
        if not bssid or not skip_next(self._stream, ",", 100):
            return None

        channel = parse_int(self._stream, 500)
        rssi = parse_int(self._stream, 500)
        if None in (channel, rssi):
            return None
        if single_find_util(self._stream, "\r\nOK\r\n", 100):
            return (ssid, bssid, channel, rssi)
        return None
