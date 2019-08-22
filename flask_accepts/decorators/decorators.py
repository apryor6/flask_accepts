from flask import jsonify
from werkzeug.wrappers import Response
from werkzeug.exceptions import BadRequest
from marshmallow import Schema

from flask_restplus.model import Model
from flask_restplus import fields, reqparse
from flask_accepts.utils import for_swagger


def accepts(
    *args,
    model_name: str = None,
    schema: Schema = None,
    many: bool = False,
    api=None,
    use_swagger: bool = True,
):
    """
    Wrap a Flask route with input validation using a combination of reqparse from
    Flask-RESTplus and/or Marshmallow schemas

    Args:
        *args: any number of dictionaries containing parameters to pass to
            reqparse.RequestParser().add_argument(). A single string parameter may also be
            provided that is used as the model name.  By default these parameters
            will be parsed using the default logic
            however, if a schema is provided then the JSON body is assumed to correspond
            to it and will not be parsed for query params
        model_name (str): the name to pass to api.Model, can optionally be provided as a str argument to *args
        schema (Marshmallow.Schema, optional): A Marshmallow Schema that will be used to parse JSON
            data from the request body and store in request.parsed_bj. Defaults to None.
        many (bool, optional): The Marshmallow schema `many` parameter, which will
            return a list of the corresponding schema objects when set to True.
    
    Returns:
        The wrapped route
    """

    # If an api was passed in, we need to use its parser so Swagger is aware
    if api:
        _parser = api.parser()
    else:
        _parser = reqparse.RequestParser(bundle_errors=True)

    query_params = [arg for arg in args if isinstance(arg, dict)]

    for arg in args:  # check for positional string-arg, which is the model name
        if isinstance(arg, str):
            model_name = arg
            break
    for qp in query_params:
        _parser.add_argument(**qp, location="values")

    def decorator(func):
        from functools import wraps

        # Check if we are decorating a class method
        _IS_METHOD = _is_method(func)

        @wraps(func)
        def inner(*args, **kwargs):
            from flask import request

            error = None
            # Handle arguments
            try:
                request.parsed_args = _parser.parse_args()
            except Exception as e:
                error = e

            # Handle Marshmallow schema
            if schema:
                obj, err = schema(many=many).load(request.get_json())
                if err:
                    error = error or BadRequest(f"Invalid parsing error: {err}")
                    if hasattr(error, "data"):
                        error.data["errors"].update({"schema_errors": err})
                    else:
                        error.data = {"schema_errors": err}
                request.parsed_obj = obj

            # If any parsing produced an error, combine them and re-raise
            if error:
                raise error

            return func(*args, **kwargs)

        # Add Swagger
        if api and use_swagger and _IS_METHOD:
            if schema:
                inner = api.doc(
                    params={qp["name"]: qp for qp in query_params},
                    body=for_swagger(schema=schema, model_name=model_name, api=api),
                )(inner)
            elif _parser:
                inner = api.expect(_parser)(inner)
        return inner

    return decorator


def responds(
    *args,
    model_name: str = None,
    schema=None,
    many: bool = False,
    api=None,
    status_code: int = 200,
    validate: bool = True,
    use_swagger: bool = True,
):
    """
    Serialize the output of a function using the Marshmallow schema to dump the results.
    Note that `schema` should be the type, not an instance -- the `responds` decorator
    will internally handle creation of the schema. If the outputted value is already of 
    type flask.Response, it will be passed along without further modification.
    
    Args:
        schema (bool, optional): Marshmallow schema with which to serialize the output
            of the wrapped function.
        many (bool, optional): The Marshmallow schema `many` parameter, which will
            return a list of the corresponding schema objects when set to True.
    
    Returns:
        The output of schema(many=many).dumps(<return value>) of the wrapped function
    """
    from functools import wraps

    from flask_restplus import reqparse

    # If an api was passed in, we need to use its parser so Swagger is aware
    if api:
        _parser = api.parser()
    else:
        _parser = reqparse.RequestParser(bundle_errors=True)

    query_params = [arg for arg in args if isinstance(arg, dict)]

    for arg in args:  # check for positional string-arg, which is the model name
        if isinstance(arg, str):
            model_name = arg
            break
    for qp in query_params:
        _parser.add_argument(**qp, location="values")

    def decorator(func):

        # Check if we are decorating a class method
        _IS_METHOD = _is_method(func)

        @wraps(func)
        def inner(*args, **kwargs):
            rv = func(*args, **kwargs)

            # If a Flask response has been made already, it is passed through unchanged
            if isinstance(rv, Response):
                return rv
            if schema:
                serialized = schema(many=many).dump(rv).data
            else:
                from flask_restplus import marshal

                serialized = marshal(rv, _model_from_parser(_parser))
                # serialized = marshal(
                # rv, Model("test", {"_id": fields.Integer, "name": fields.String})
                # )
            if not _is_method(func):
                # Regular route, need to manually create Response
                return jsonify(serialized), status_code
            return serialized, status_code

        # Add Swagger
        if api and use_swagger and _IS_METHOD:
            if schema:
                inner = _document_like_marshal_with(
                    for_swagger(schema=schema, model_name=model_name, api=api),
                    status_code=status_code,
                )(inner)

            elif _parser:
                inner = api.expect(_parser)(inner)

        return inner

    return decorator


def _model_from_parser(_parser: reqparse.RequestParser) -> Model:
    from flask_restplus import fields

    base_type_map = {
        "integer": fields.Integer,
        "string": fields.String,
        "number": fields.Float,
    }
    type_factory = {
        "integer": lambda arg: base_type_map["integer"],
        "string": lambda arg: base_type_map["string"],
        "number": lambda arg: base_type_map["number"],
        "array": lambda arg: fields.List(base_type_map[arg["items"]["type"]]),
    }
    return Model(
        "responds",
        {arg["name"]: type_factory[arg["type"]](arg) for arg in _parser.__schema__},
    )


def merge(first: dict, second: dict) -> dict:
    return {**first, **second}


def _document_like_marshal_with(values, status_code: int = 200):
    def inner(func):
        description = "a test description"
        doc = {"responses": {status_code: (description, values)}, "__mask__": True}
        func.__apidoc__ = merge(getattr(func, "__apidoc__", {}), doc)
        return func

    return inner


def _is_method(func):
    """
    Check is function is defined inside a class.
    ASSUMES YOU ARE USING THE CONVENTION THAT FIRST ARG IS 'self'
    """
    import inspect

    sig = inspect.signature(func)
    return "self" in sig.parameters
