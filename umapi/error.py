class UMAPIError(Exception):
    def __init__(self, res):
        Exception.__init__(self, "UMAPI Error: "+str(res.status_code))
        self.res = res


class UMAPIRetryError(UMAPIError):
    pass
