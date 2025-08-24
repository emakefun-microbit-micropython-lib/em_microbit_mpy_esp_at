from esp_at_result_code import ResultCode


class ResultData:
    def __init__(self, code: int, **fields):
        self._code = code
        self._fields = fields

    @property
    def is_ok(self):
        return self._code == ResultCode.OK

    def __getattr__(self, name):
        if name in self._fields:
            return self._fields[name]
        raise AttributeError(
            "'{}' object has no attribute '{}'".format(self.__class__.__name__, name)
        )

    def __str__(self):
        if self.is_ok:
            items = []
            for key, value in self._fields.items():
                rep = '"{}"'.format(value) if isinstance(value, str) else str(value)
                items.append("{}={}".format(key, rep))
            return "Success: {}".format(", ".join(items))
        else:
            return "Error: {}".format(self.code.name)
