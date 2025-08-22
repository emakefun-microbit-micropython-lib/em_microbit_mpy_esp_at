from micropython import const


class ResultCode:
    OK: int = const(0)
    ERROR: int = const(1)
    BUSY: int = const(2)
    TIMEDOUT: int = const(3)
    INVALID_PARAMETERS: int = const(4)

    @staticmethod
    def to_string(code: int):
        codes = {
            ResultCode.OK: "OK",
            ResultCode.ERROR: "Error",
            ResultCode.BUSY: "Busy",
            ResultCode.TIMEDOUT: "Timedout",
            ResultCode.INVALID_PARAMETERS: "InvalidParameters",
        }
        return codes.get(code, "Unknown ResultCode")
