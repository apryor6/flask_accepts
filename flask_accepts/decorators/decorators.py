def accepts(*args, schema=None):
    """
    Wrap a Flask route with input validation

    Args:
        *args: any number of dictionaries containing parameters to pass to
            reqparse.RequestParser().add_argument(). By default these parameters
            will be parsed using the default logic (see https://flask-restful.readthedocs.io/en/0.3.5/reqparse.html#argument-locations);
            however, if a schema is provided then the JSON body is assumed to correspond
            to it and will not be parsed for query params
        schema ([type], optional): A Marshmallow Schema that will be used to parse JSON
            data from the request body and store in request.parsed_bj. Defaults to None.

    Returns:
        The wrapped route
    """
    from flask_restful import reqparse

    _parser = reqparse.RequestParser(bundle_errors=True)
    for arg in args:
        if isinstance(arg, dict):
            _parser.add_argument(**arg, location='values')

    def decorator(func):
        from functools import wraps
        @wraps(func)
        def inner(*args, **kwargs):
            from flask import request
            error = {}
            try:
                request.parsed_args = _parser.parse_args()
            except Exception as e:
                error = e
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


def responds(*args, schema=None):
    def decorator(func):
        from functools import wraps
        @wraps(func)
        def inner(*args, **kwargs):
            rv = func(*args, **kwargs)
            return schema().dump(rv)
        return inner
    return decorator
