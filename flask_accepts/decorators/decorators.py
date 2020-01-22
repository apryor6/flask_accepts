from typing import Type, Union
from flask import jsonify
from werkzeug.wrappers import Response
from werkzeug.exceptions import BadRequest, InternalServerError
from marshmallow import Schema
from marshmallow.exceptions import ValidationError

from flask_restx.model import Model
from flask_restx import fields, reqparse, inputs
from flask_accepts.utils import for_swagger, get_default_model_name


def accepts(
    *args,
    model_name: str = None,
    schema: Union[Schema, Type[Schema], None] = None,
    many: bool = False,
    api=None,
    use_swagger: bool = True,
):
    """
    Wrap a Flask route with input validation using a combination of reqparse from
    Flask-restx and/or Marshmallow schemas

    Args:
        *args: any number of dictionaries containing parameters to pass to
            reqparse.RequestParser().add_argument(). A single string parameter may also be
            provided that is used as the model name.  By default these parameters
            will be parsed using the default logic
            however, if a schema is provided then the JSON body is assumed to correspond
            to it and will not be parsed for query params
        model_name (str): the name to pass to api.Model, can optionally be provided as a str argument to *args
        schema (Marshmallow.Schema, optional): A Marshmallow Schema that will be used to parse JSON
            data from the request body and
            store in request.parsed_bj. Defaults to None.
        many (bool, optional): The Marshmallow schema `many` parameter, which will
            return a list of the corresponding schema objects when set to True.

    Returns:
        The wrapped route
    """

    _check_deprecate_many(many)

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
        params = {**qp, "location": qp.get("location") or "values"}
        if qp["type"] == bool:
            # mapping native bool is necessary so that string "false" is not truthy
            # https://flask-restx.readthedocs.io/en/stable/parsing.html#advanced-types-handling
            params['type'] = inputs.boolean
        _parser.add_argument(**params)

    if schema:
        schema = _get_or_create_schema(schema, many=many)

    def decorator(func):
        from functools import wraps

        # Check if we are decorating a class method
        _IS_METHOD = _is_method(func)

        @wraps(func)
        def inner(*args, **kwargs):
            from flask import request

            error = schema_error = None
            # Handle arguments
            try:
                request.parsed_args = _parser.parse_args()
            except Exception as e:
                error = e

            # Handle Marshmallow schema
            if schema:
                try:
                    obj = schema.load(request.get_json())
                    request.parsed_obj = obj
                except ValidationError as ex:
                    schema_error = ex.messages
                if schema_error:
                    error = error or BadRequest(
                        f"Invalid parsing error: {schema_error}"
                    )
                    if hasattr(error, "data"):
                        error.data["errors"].update({"schema_errors": schema_error})
                    else:
                        error.data = {"schema_errors": schema_error}

            # If any parsing produced an error, combine them and re-raise
            if error:
                raise error

            return func(*args, **kwargs)

        # Add Swagger
        if api and use_swagger and _IS_METHOD:
            if schema:
                body = for_swagger(
                    schema=schema,
                    model_name=model_name or get_default_model_name(schema),
                    api=api,
                    operation="load",
                )
                params = {
                    'expect': [body, _parser],
                }
                inner = api.doc(**params)(inner)
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
    validate: bool = False,
    description: str = None,
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
        many (bool, optional): (DEPRECATED) The Marshmallow schema `many` parameter, which will
            return a list of the corresponding schema objects when set to True.

    Returns:
        The output of schema(many=many).dumps(<return value>) of the wrapped function
    """
    from functools import wraps

    from flask_restx import reqparse

    _check_deprecate_many(many)

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

    if schema:
        schema = _get_or_create_schema(schema, many=many)

    model_name = model_name or get_default_model_name(schema)
    model_from_parser = _model_from_parser(model_name=model_name, parser=_parser)

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
                serialized = schema.dump(rv)

                # Validate data if asked to (throws)
                if validate:
                    errs = schema.validate(serialized)
                    if errs:
                        raise InternalServerError(
                            description="Server attempted to return invalid data"
                        )
            else:
                from flask_restx import marshal

                serialized = marshal(rv, model_from_parser)

            if not _is_method(func):
                # Regular route, need to manually create Response
                return jsonify(serialized), status_code
            return serialized, status_code

        # Add Swagger
        if api and use_swagger and _IS_METHOD:
            if schema:
                api_model = for_swagger(
                    schema=schema, model_name=model_name, api=api, operation="dump"
                )
                if schema.many is True:
                    api_model = [api_model]

                inner = _document_like_marshal_with(
                    api_model,
                    status_code=status_code,
                    description=description,
                )(inner)

            elif _parser:
                api.add_model(model_name, model_from_parser)
                inner = _document_like_marshal_with(
                    model_from_parser, status_code=status_code
                )(inner)

        return inner

    return decorator


def _check_deprecate_many(many: bool = False):
    if many:
        import warnings

        warnings.simplefilter("always", DeprecationWarning)
        warnings.warn(
            "The 'many' parameter is deprecated in favor of passing these "
            "arguments to an actual instance of Marshmallow schema (i.e. "
            "prefer @responds(schema=MySchema(many=True)) instead of "
            "@responds(schema=MySchema, many=True))",
            DeprecationWarning,
            stacklevel=3,
        )


def _get_or_create_schema(
    schema: Union[Schema, Type[Schema]], many: bool = False
) -> Schema:
    if isinstance(schema, Schema):
        return schema
    return schema(many=many)


def _model_from_parser(model_name: str, parser: reqparse.RequestParser) -> Model:
    from flask_restx import fields

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
        model_name,
        {arg["name"]: type_factory[arg["type"]](arg) for arg in parser.__schema__},
    )


def merge(first: dict, second: dict) -> dict:
    return {**first, **second}


def _document_like_marshal_with(
    values, status_code: int = 200, description: str = None
):
    description = description or "Success"

    def inner(func):
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
