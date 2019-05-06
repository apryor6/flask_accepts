from flask_restplus import fields as fr
from marshmallow import fields as ma

type_map = {
    ma.Integer: fr.Integer,
    ma.Float: fr.Float,
    ma.String: fr.String,
}


def for_swagger(schema, api):
    """
    Convert a marshmallow schema to equivalent Flask-RESTful model

    Args:
        schema (Marshmallow Schema): Schema defining the inputs
        api (Namespace): Flask-RESTful namespace (necessary for context)

    Returns:
        api.model: An equivalent api.model
    """
    fields = {k: type_map[type(v)] for k, v in
              vars(schema()).get('declared_fields', {}).items()
              if type(v) in type_map}
    return api.model(api.name, fields)
