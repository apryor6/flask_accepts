"""An example of Marshmallow validators within flask_accepts"""

from dataclasses import dataclass
from marshmallow import fields, Schema, post_load, validate
from flask import Flask, jsonify, request
from flask_accepts import accepts, responds

from datetime import datetime


@dataclass
class Doodad:
    name: str
    when: datetime
    is_on: bool


class DoodadSchema(Schema):
    name = fields.String()
    when = fields.DateTime()
    is_on = fields.Boolean()

    @post_load
    def make(self, data, **kwargs):
        return Doodad(**data)


def create_app(env=None):
    from flask_restx import Api, Namespace, Resource

    app = Flask(__name__)
    api = Api(app)

    @api.route("/restx/make_a_widget")
    class DoodadResource(Resource):
        @accepts(schema=DoodadSchema, api=api)
        @responds(schema=DoodadSchema, api=api)
        def post(self):
            from flask import jsonify

            return request.parsed_obj

    return app


app = create_app()
if __name__ == "__main__":
    app.run(debug=True)
