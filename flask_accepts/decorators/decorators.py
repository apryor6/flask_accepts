from collections import OrderedDict
from typing import Type, Union
from flask import jsonify
from werkzeug.wrappers import Response
from werkzeug.exceptions import BadRequest, InternalServerError
from marshmallow import Schema, EXCLUDE, RAISE
from marshmallow.fields import List
from marshmallow.exceptions import ValidationError

from flask_restx.model import Model
from flask_restx import fields, reqparse, inputs
from flask_accepts.utils import for_swagger, get_default_model_name, is_list_field, ma_field_to_reqparse_argument


def accepts(
    *args,
    model_name: str = None,
    schema: Union[Schema, Type[Schema], None] = None,
    query_params_schema: Union[Schema, Type[Schema], None] = None,
    headers_schema: Union[Schema, Type[Schema], None] = None,
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
            will be parsed using the default logic however, if a schema is provided then
            the JSON body is assumed to correspond to it and will not be parsed for query params.
        model_name (str): the name to pass to api.Model, can optionally be provided as a str argument to *args
        schema (Marshmallow.Schema, optional): A Marshmallow Schema that will be used to parse JSON
            data from the request body and store in request.parsed_obj. Defaults to None.
        query_params_schema (Marshmallow.Schema, optional): A Marshmallow Schema that will be used to parse
            data from the request query params and store in request.parsed_query_params. These values will
            also be added to the `request.args` dict. Defaults to None.
        headers_schema (Marshmallow.Schema, optional): A Marshmallow Schema that will be used to parse
            data from the request header and store in request.parsed_headers. Defaults to None.
        many (bool, optional): The Marshmallow schema `many` parameter, which will
            return a list of the corresponding schema objects when set to True. This
            flag corresopnds only to the request body schema, and not the
            `query_params_schema` or `headers_schema` arguments.

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

    # Handles query params passed in as positional arguments.
    for qp in query_params:
        params = {**qp, "location": qp.get("location") or "values"}
        if qp["type"] == bool:
            # mapping native bool is necessary so that string "false" is not truthy
            # https://flask-restx.readthedocs.io/en/stable/parsing.html#advanced-types-handling
            params["type"] = inputs.boolean
        _parser.add_argument(**params)

    # Handles request body schema.
    if schema:
        schema = _get_or_create_schema(schema, many=many)

    # Handles query params schema.
    if query_params_schema:
        query_params_schema = _get_or_create_schema(query_params_schema, unknown=EXCLUDE)

        for name, field in query_params_schema.fields.items():
            params = {**ma_field_to_reqparse_argument(field), "location": "values"}
            _parser.add_argument(name, **params)

    # Handles headers schema.
    if headers_schema:
        headers_schema = _get_or_create_schema(headers_schema, unknown=EXCLUDE)

        for name, field in headers_schema.fields.items():
            params = {**ma_field_to_reqparse_argument(field), "location": "headers"}
            _parser.add_argument(name, **params)

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

            # Handle Marshmallow schema for request body
            if schema:
                try:
                    obj = schema.load(request.get_json(force=True))
                    request.parsed_obj = obj
                except ValidationError as ex:
                    schema_error = ex.messages
                if schema_error:
                    error = error or BadRequest(
                        f"Error parsing request body: {schema_error}"
                    )
                    if hasattr(error, "data"):
                        error.data["errors"].update({"schema_errors": schema_error})
                    else:
                        error.data = {"schema_errors": schema_error}

            # Handle Marshmallow schema for query params
            if query_params_schema:
                request_args = _convert_multidict_values_to_schema(
                    request.args,
                    query_params_schema)

                try:
                    obj = query_params_schema.load(request_args)
                    request.parsed_query_params = obj
                except ValidationError as ex:
                    schema_error = ex.messages
                if schema_error:
                    error = error or BadRequest(
                        f"Error parsing query params: {schema_error}"
                    )
                    if hasattr(error, "data"):
                        error.data["errors"].update({"schema_errors": schema_error})
                    else:
                        error.data = {"schema_errors": schema_error}

            # Handle Marshmallow schema for headers
            if headers_schema:
                request_headers = _convert_multidict_values_to_schema(
                    request.headers,
                    headers_schema)

                try:
                    obj = headers_schema.load(request_headers)
                    request.parsed_headers = obj
                except ValidationError as ex:
                    schema_error = ex.messages
                if schema_error:
                    error = error or BadRequest(
                        f"Error parsing headers: {schema_error}"
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
                if schema.many is True:
                    body = [body]

                params = {
                    "expect": [body, _parser],
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
    envelope=None,
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

    ordered = None
    if schema:
        schema = _get_or_create_schema(schema, many=many)
        ordered = schema.ordered

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

                # Apply the flask-restx mask after validation
                serialized = _apply_restx_mask(serialized)
            else:
                from flask_restx import marshal

                serialized = marshal(rv, model_from_parser)

            if envelope:
                serialized = OrderedDict([(envelope, serialized)]) if ordered else {envelope: serialized}

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
                    api_model, status_code=status_code, description=description,
                )(inner)

            elif _parser:
                api.add_model(model_name, model_from_parser)
                inner = _document_like_marshal_with(
                    model_from_parser, status_code=status_code, description=description
                )(inner)

        return inner

    return decorator


def _apply_restx_mask(serialized):
    from flask import current_app, request
    from flask_restx.mask import apply as apply_mask

    mask_header = current_app.config.get("RESTX_MASK_HEADER", "X-Fields")
    mask = request.headers.get(mask_header)
    return apply_mask(serialized, mask) if mask else serialized


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
    schema: Union[Schema, Type[Schema]], many: bool = False, unknown: str = RAISE
) -> Schema:
    if isinstance(schema, Schema):
        return schema
    return schema(many=many, unknown=unknown)


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


def _convert_multidict_values_to_schema(multidict, schema):
    """Helper function that converts values in the given multidict into either
    single or list values based on the schema definition.

    This function is necessary for parsing multidict mappings like querystrings
    where it's ambiguous whether the value is single or list value. Take the
    following query string as an example:

        ?foo=bar

    In this case, `foo` could map to a single string `'bar'`, or a list with
    one string element `['bar']`.

    This function looks at the given `schema` and converts the values in the
    given `multidict` appropriately to be parsed be loaded by `marshmallow`
    later on.
    """
    result = {}

    fields = dict(schema.fields.items())
    for key, value in multidict.items():
        # If the key isn't defined in the schema, then insert it into the
        # result set as is and let marshmallow validation raise an error.
        if key not in fields:
            result[key] = value
        # If the corresponding field is a list, then make sure to return the
        # value as a list.
        elif is_list_field(fields[key]):
            result[key] = multidict.getlist(key)
        else:
            result[key] = value

    return result
