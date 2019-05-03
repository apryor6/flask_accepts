def accepts(*args):
    from flask_restful import reqparse
    parser = [arg for arg in args if isinstance(arg, reqparse.RequestParser)]
    parser = (parser and parser[0]) or reqparse.RequestParser(bundle_errors=True)
    for arg in args:
        if isinstance(arg, dict):
            parser.add_argument(**arg)

    def decorator(func):
        from functools import wraps
        @wraps(func)
        def inner(*args, **kwargs):
            from flask import request
            request.parsed_args = parser.parse_args()
            return func(*args, **kwargs)
        return inner
    return decorator
