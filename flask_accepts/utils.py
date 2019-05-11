from flask_restplus import fields as fr
from marshmallow import fields as ma
from marshmallow.schema import Schema, SchemaMeta
import uuid


def unpack_list(val, api):
    # Unpacks a List. Only does one level for now. Eventually should make recursive.
    return fr.List(map_type(val.container, api))


def unpack_nested(val, api):
    # Unpacks a nested value. Only does one level for now. Eventually should make recursive.
    # return fr.Nested(for_swagger(map_type(val.nested, api), api=api))
    return fr.Nested(map_type(val.nested, api))


def for_swagger(schema, api):
    """
    Convert a marshmallow schema to equivalent Flask-RESTful model

    Args:
        schema (Marshmallow Schema): Schema defining the inputs
        api (Namespace): Flask-RESTful namespace (necessary for context)

    Returns:
        api.model: An equivalent api.model
    """
    fields = {k: map_type(v, api) for k, v in
              vars(schema()).get('declared_fields', {}).items()
              if type(v) in type_map}
    return api.model(str(uuid.uuid4()), fields)


type_map = {
    ma.Integer: lambda x, _: fr.Integer(),
    ma.Number: lambda x, _: fr.Float(),
    ma.Float: lambda x, _: fr.Float(),
    ma.String: lambda x, _: fr.String(),
    ma.List: unpack_list,
    ma.Nested: unpack_nested,
    SchemaMeta: for_swagger,
    Schema: for_swagger
}


def map_type(val, api):
    return type_map[type(val)](val, api)
