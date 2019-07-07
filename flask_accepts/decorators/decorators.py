from werkzeug.wrappers import Response

from flask_accepts.utils import for_swagger


def accepts(*args, schema=None, many=False, api=None, use_swagger=True):
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
    try:
        from flask_restplus import reqparse
    except ImportError:
        try:
            from flask_restful import reqparse
        except ImportError as e:
            raise e

    # If an api was passed in, we need to use its parser so Swagger is aware
    if api:
        _parser = api.parser()
    else:
        _parser = reqparse.RequestParser(bundle_errors=True)

    query_params = [arg for arg in args if isinstance(arg, dict)]
    for qp in query_params:
        _parser.add_argument(**qp, location='values')
    # for arg in args:
        # if isinstance(arg, dict):
        # _parser.add_argument(**arg, location='values')

    def decorator(func):
        from functools import wraps
        _IS_METHOD = _is_method(func)
        @wraps(func)
        def inner(*args, **kwargs):
            from flask import request
            error = None
            # Handle arguments
            try:
                request.parsed_args = _parser.parse_args()
                print('request.parsed_args = ', request.parsed_args)
            except Exception as e:
                error = e
            # Handle Marshmallow schema
            if schema:
                obj, err = schema(many=many).load(request.get_json())
                if err:
                    error = error or ValueError('Invalid parsing error.')
                    if hasattr(error, 'data'):
                        error.data['message'].update({'schema_errors': err})
                    else:
                        error.data = {'schema_errors': err}
                request.parsed_obj = obj
            # If any parsing produced an error, combine them and re-raise
            if error:
                raise(error)

            return func(*args, **kwargs)

        # Add Swagger. Currently this supports schema OR reqparse args, but not both
        if api and use_swagger and _IS_METHOD:
            if schema:
                inner = api.doc(
                    params={qp['name']: qp for qp in query_params},
                    body=for_swagger(
                        schema=schema, api=api))(inner)
            elif _parser:
                inner = api.expect(_parser)(inner)
        return inner
    return decorator


def responds(*args, schema=None, many=False):
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            rv = func(*args, **kwargs)

            # If a Flask response has been made already, it is passed through unchanged
            if isinstance(rv, Response):
                return rv
            return schema(many=many).dump(rv)
        return inner
    return decorator


def _is_method(func):
    """
    Check is function is defined inside a class.
    ASSUMES YOU ARE USING THE CONVENTION THAT FIRST ARG IS 'self'
    """
    import inspect
    sig = inspect.signature(func)
    return 'self' in sig.parameters
