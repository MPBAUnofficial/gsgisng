class GeoTreeError(RuntimeError):
    def __init__(self, message):
        RuntimeError.__init__(self, message)
