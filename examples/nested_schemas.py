from dataclasses import dataclass
from marshmallow import fields, Schema, post_load
from flask import Flask, jsonify, request
from flask_accepts import accepts, responds

from flask_restx import Api, Namespace, Resource

app = Flask(__name__)
api = Api(app)


class CogSchema(Schema):
    cog_foo = fields.String(default="cog")
    cog_baz = fields.Integer(default=999)


class WidgetSchema(Schema):
    foo = fields.String(default="test string")
    baz = fields.Integer(default=42)
    flag = fields.Bool(default=False)
    date = fields.Date(default="01-01-1900")
    dec = fields.Decimal(default=42.42)
    dct = fields.Dict(default={"key": "value"})

    cog = fields.Nested(CogSchema)


@api.route("/restx/make_a_widget")
class WidgetResource(Resource):
    @accepts(dict(name="some_arg", type=str), schema=CogSchema, api=api)
    @responds(schema=CogSchema, api=api)
    def get(self):
        from flask import jsonify

        return request.parsed_obj

    @accepts(dict(name="some_arg", type=str), schema=WidgetSchema, api=api)
    @responds(schema=WidgetSchema, api=api)
    def post(self):
        from flask import jsonify

        return request.parsed_obj


if __name__ == "__main__":
    app.run(debug=True)
