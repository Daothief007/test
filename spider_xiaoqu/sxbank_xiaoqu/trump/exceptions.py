from sanic.exceptions import SanicException

class Unauthorized(SanicException):
    status_code = 401


