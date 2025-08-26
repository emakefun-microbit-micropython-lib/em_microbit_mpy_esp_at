class ResultData:
    def __init__(self, success: bool, **fields):
        self.success = success
        self._fields = fields

    def __getattr__(self, name):
        if name in self._fields:
            return self._fields[name]
        raise AttributeError(
            "'{}' object has no attribute '{}'".format(self.__class__.__name__, name)
        )
