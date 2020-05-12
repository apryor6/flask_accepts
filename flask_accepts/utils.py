from typing import Optional, Type, Union
from flask_restx import fields as fr, inputs
from marshmallow import fields as ma
from marshmallow.schema import Schema, SchemaMeta
import uuid


def unpack_list(val, api, model_name: str = None, operation: str = "dump"):
    model_name = model_name or get_default_model_name()
    return fr.List(
        map_type(val.inner, api, model_name, operation), **_ma_field_to_fr_field(val)
    )


def unpack_nested(val, api, model_name: str = None, operation: str = "dump"):
    if val.nested == "self":
        return unpack_nested_self(val, api, model_name, operation)

    model_name = get_default_model_name(val.nested)
    return fr.Nested(
        map_type(val.nested, api, model_name, operation), **_ma_field_to_fr_field(val)
    )


def unpack_nested_self(val, api, model_name: str = None, operation: str = "dump"):
    model_name = model_name or get_default_model_name(val.schema)
    fields = {
        k: map_type(v, api, model_name, operation)
        for k, v in (vars(val.schema).get("fields").items())
        if type(v) in type_map and _check_load_dump_only(v, operation)
    }
    if val.many:
        return fr.List(
            fr.Nested(
                api.model(f"{model_name}-child", fields), **_ma_field_to_fr_field(val)
            )
        )
    else:
        return fr.Nested(
            api.model(f"{model_name}-child", fields), **_ma_field_to_fr_field(val)
        )


def for_swagger(schema, api, model_name: str = None, operation: str = "dump"):
    """
    Convert a marshmallow schema to equivalent Flask-restx model

    Args:
        schema (Marshmallow Schema): Schema defining the inputs
        api (Namespace): Flask-restx namespace (necessary for context)
        model_name (str): Name of Flask-restx model

    Returns:
        api.model: An equivalent api.model
    """

    model_name = model_name or get_default_model_name(schema)

    # For nested Schemas, the internal fields are stored in _declared_fields, whereas
    # for Schemas the name is declared_fields, so check for both.
    if isinstance(schema, SchemaMeta):
        schema = schema()
    fields = {
        v.data_key or k: map_type(v, api, model_name, operation)
        for k, v in (vars(schema).get("fields").items())
        if type(v) in type_map and _check_load_dump_only(v, operation)
    }

    model_name = _maybe_add_operation(schema, model_name, operation)
    return api.model(model_name, fields)


def _maybe_add_operation(schema, model_name: str, operation: str):
    if any(f.load_only or f.dump_only for k, f in (vars(schema).get("fields").items())):
        return f"{model_name}-{operation}"
    return f"{model_name}"


def _check_load_dump_only(field: ma.Field, operation: str) -> bool:
    if operation == "dump":
        return not field.load_only
    elif operation == "load":
        return not field.dump_only
    else:
        raise ValueError(
            f"Invalid operation: {operation}. Options are 'load' and 'dump'."
        )


def make_type_mapper(field_type):
    """Factory for creating mapping functions for `type_map` with additional
    marshmallow fields, if present"""

    def mapper(val, api, model_name, operation):
        return field_type(**_ma_field_to_fr_field(val))

    return mapper


type_map = {
    ma.AwareDateTime: fr.Raw,
    ma.Bool: fr.Boolean,
    ma.Boolean: fr.Boolean,
    ma.Constant: fr.Raw,
    ma.Date: fr.Date,
    ma.DateTime: fr.DateTime,
    # For some reason, fr.Decimal has no example parameter, so use Float instead
    ma.Decimal: fr.Float,
    ma.Dict: fr.Raw,
    ma.Email: fr.String,
    ma.Float: fr.Float,
    ma.Function: fr.Raw,
    ma.Int: fr.Integer,
    ma.Integer: fr.Integer,
    ma.Length: fr.Float,
    ma.Mapping: fr.Raw,
    ma.Method: fr.Raw,
    ma.NaiveDateTime: fr.DateTime,
    ma.Number: fr.Float,
    ma.Pluck: fr.Raw,
    ma.Raw: fr.Raw,
    ma.Str: fr.String,
    ma.String: fr.String,
    ma.Time: fr.DateTime,
    ma.Url: fr.Url,
    ma.URL: fr.Url,
    ma.UUID: fr.String,
}


type_map = {k: make_type_mapper(v) for k, v in type_map.items()}

# Add in the special cases
type_map.update(
    {
        ma.List: unpack_list,
        ma.Nested: unpack_nested,
        Schema: for_swagger,
        SchemaMeta: for_swagger,
    }
)

num_default_models = 0


def get_default_model_name(schema: Optional[Union[Schema, Type[Schema]]] = None) -> str:
    if schema:
        if isinstance(schema, Schema):
            return "".join(schema.__class__.__name__.rsplit("Schema", 1))
        else:
            # It is a type itself
            return "".join(schema.__name__.rsplit("Schema", 1))

    global num_default_models
    name = f"DefaultResponseModel_{num_default_models}"
    num_default_models += 1
    return name


def _ma_field_to_fr_field(value: ma.Field) -> dict:
    fr_field_parameters = {}

    if hasattr(value, "default"):
        fr_field_parameters["example"] = value.default

    if hasattr(value, "required"):
        fr_field_parameters["required"] = value.required

    if hasattr(value, "metadata") and "description" in value.metadata:
        fr_field_parameters["description"] = value.metadata["description"]

    if hasattr(value, "missing") and type(value.missing) != ma.utils._Missing:
        fr_field_parameters["default"] = value.missing

    return fr_field_parameters


def map_type(val, api, model_name, operation):
    value_type = type(val)

    if value_type in type_map:
        return type_map[value_type](val, api, model_name, operation)

    if issubclass(value_type, SchemaMeta) or issubclass(value_type, Schema):
        return type_map[Schema](val, api, model_name, operation)

    raise TypeError('Unknown type for marshmallow model field was used.')


type_map_ma_to_reqparse = {
    ma.Bool: inputs.boolean,
    ma.Boolean: inputs.boolean,
    ma.Int: int,
    ma.Integer: int,
    ma.Float: float
}


def ma_field_to_reqparse_argument(value: ma.Field) -> dict:
    """Maps a marshmallow field to a dictionary that can be used to initialize a
    request parser argument.
    """
    reqparse_argument_parameters = {}

    if is_list_field(value):
        value_type = type(value.inner)
        reqparse_argument_parameters["action"] = "append"
    else:
        value_type = type(value)
        reqparse_argument_parameters["action"] = "store"

    reqparse_argument_parameters["type"] = type_map_ma_to_reqparse.get(value_type, str)

    if hasattr(value, "required"):
        reqparse_argument_parameters["required"] = value.required

    if hasattr(value, "metadata") and "description" in value.metadata:
        reqparse_argument_parameters["help"] = value.metadata["description"]

    return reqparse_argument_parameters


def is_list_field(field):
    """Returns `True` if the given field is a list type."""
    # Need to handle both flask_restx and marshmallow fields.
    return isinstance(field, ma.List) or isinstance(field, fr.List)
