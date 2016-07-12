class UMAPIError(Exception):
    def __init__(self, res):
        Exception.__init__(self, "UMAPI Error: "+str(res.status_code))
        self.res = res


class UMAPIRetryError(Exception):
    def __init__(self, res):
        Exception.__init__(self, "UMAPI Error: "+str(res.status_code))
        self.res = res


class UMAPIRequestError(Exception):
    def __init__(self, code):
        Exception.__init__(self, "Request Error -- %s" % code)
        self.code = code


class ActionFormatError(Exception):
    pass
