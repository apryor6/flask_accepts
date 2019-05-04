def accepts(*args, schema=None):
    from flask_restful import reqparse

    _parser = reqparse.RequestParser(bundle_errors=True)
    for arg in args:
        if isinstance(arg, dict):
            _parser.add_argument(**arg)

    def decorator(func):
        from functools import wraps
        @wraps(func)
        def inner(*args, **kwargs):
            from flask import request
            error = {}
            try:
                request.parsed_args = _parser.parse_args()
            except Exception as e:
                # print('E = ', e)
                error = e
                # raise(e)
            if schema:
                obj, err = schema().load(request.get_json())
                if err:
                    error.data['message'].update({'schema_errors': err})
                request.parsed_obj = obj
            if error:
                raise(error)
            return func(*args, **kwargs)
        return inner
    return decorator
