from typing import Optional, Type, Union
from flask_restplus import fields as fr
from marshmallow import fields as ma
from marshmallow.schema import Schema, SchemaMeta
import uuid


def unpack_list(val, api, model_name: str = None):
    model_name = model_name or get_default_model_name()
    return fr.List(map_type(val.inner, api, model_name))


def unpack_nested(val, api, model_name: str = None):
    model_name = get_default_model_name(val.nested)
    return fr.Nested(map_type(val.nested, api, model_name))


def for_swagger(schema, api, model_name: str = None, operation="dump"):
    """
    Convert a marshmallow schema to equivalent Flask-RESTplus model

    Args:
        schema (Marshmallow Schema): Schema defining the inputs
        api (Namespace): Flask-RESTplus namespace (necessary for context)
        model_name (str): Name of Flask-RESTplus model

    Returns:
        api.model: An equivalent api.model
    """

    model_name = model_name or get_default_model_name(schema)

    # For nested Schemas, the internal fields are stored in _declared_fields, whereas
    # for Schemas the name is declared_fields, so check for both.
    if isinstance(schema, SchemaMeta):
        schema = schema()

    fields = {
        k: map_type(v, api, model_name)
        for k, v in (vars(schema).get("fields").items())
        if type(v) in type_map and _check_load_dump_only(v, operation)
    }

    return api.model("{}-{}".format(model_name, operation), fields)


def _check_load_dump_only(field: ma.Field, operation: str) -> bool:
    if operation == "dump":
        return not field.load_only
    elif operation == "load":
        return not field.dump_only
    else:
        raise ValueError(
            f"Invalid operation: {operation}. Options are 'load' and 'dump'."
        )


type_map = {
    ma.AwareDateTime: lambda val, api, model_name: fr.Raw(example=val.default),
    ma.Bool: lambda val, api, model_name: fr.Boolean(example=val.default),
    ma.Boolean: lambda val, api, model_name: fr.Boolean(example=val.default),
    ma.Constant: lambda val, api, model_name: fr.Raw(example=val.default),
    ma.Date: lambda val, api, model_name: fr.Date(example=val.default),
    ma.DateTime: lambda val, api, model_name: fr.DateTime(example=val.default),
    # For some reason, fr.Decimal has no example parameter, so use Float instead
    ma.Decimal: lambda val, api, model_name: fr.Float(example=val.default),
    ma.Dict: lambda val, api, model_name: fr.Raw(example=val.default),
    ma.Email: lambda val, api, model_name: fr.String(example=val.default),
    ma.Float: lambda val, api, model_name: fr.Float(example=val.default),
    ma.Function: lambda val, api, model_name: fr.Raw(example=val.default),
    ma.Int: lambda val, api, model_name: fr.Integer(example=val.default),
    ma.Integer: lambda val, api, model_name: fr.Integer(example=val.default),
    ma.Length: lambda val, api, model_name: fr.Float(example=val.default),
    ma.Mapping: lambda val, api, model_name: fr.Raw(example=val.default),
    ma.NaiveDateTime: lambda val, api, model_name: fr.DateTime(example=val.default),
    ma.Number: lambda val, api, model_name: fr.Float(example=val.default),
    ma.Pluck: lambda val, api, model_name: fr.Raw(example=val.default),
    ma.Raw: lambda val, api, model_name: fr.Raw(example=val.default),
    ma.Str: lambda val, api, model_name: fr.String(example=val.default),
    ma.String: lambda val, api, model_name: fr.String(example=val.default),
    ma.Time: lambda val, api, model_name: fr.DateTime(example=val.default),
    ma.Url: lambda val, api, model_name: fr.Url(example=val.default),
    ma.URL: lambda val, api, model_name: fr.Url(example=val.default),
    ma.UUID: lambda val, api, model_name: fr.String(example=val.default),
    ma.List: unpack_list,
    ma.Nested: unpack_nested,
    Schema: for_swagger,
    SchemaMeta: for_swagger,
}

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


def map_type(val, api, model_name):
    return type_map[type(val)](val, api, model_name)
