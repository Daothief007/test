from sanic import Sanic

class Trump(Sanic):
    def __init__(self, name=None, router=None,
            error_handler=None, session=None):
        super(Trump, self).__init__(
            name = name,
            router = router,
            error_handler = error_handler
        )
