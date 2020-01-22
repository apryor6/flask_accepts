"""An example of Marshmallow validators within flask_accepts"""

from dataclasses import dataclass
from marshmallow import fields, Schema, post_load, validate
from flask import Flask, jsonify, request
from flask_accepts import accepts, responds


@dataclass
class Widget:
    foo: str
    baz: int


class WidgetSchema(Schema):
    foo = fields.String(validate=validate.Length(min=3))
    baz = fields.Integer()

    @post_load
    def make(self, data, **kwargs):
        return Widget(**data)


def create_app(env=None):
    from flask_restx import Api, Namespace, Resource

    app = Flask(__name__)
    api = Api(app)

    @api.route("/restx/make_a_widget")
    class WidgetResource(Resource):
        @accepts(schema=WidgetSchema, api=api)
        @responds(schema=WidgetSchema, api=api)
        def post(self):
            from flask import jsonify

            return request.parsed_obj

    return app


app = create_app()
if __name__ == "__main__":
    app.run(debug=True)
