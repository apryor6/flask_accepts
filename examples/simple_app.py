from flask import Flask, request
from flask_accepts import accepts
from flask_restx import Api, Namespace, Resource
from marshmallow import Schema, fields


class TestSchema(Schema):
    id = fields.Integer(attribute="id")


class HigherSchema(Schema):
    id = fields.Integer(attribute="id")
    _list = fields.List(fields.Integer())
    test = fields.Nested(TestSchema, attribute="test")
    list_nested = fields.List(fields.Nested(TestSchema))


o = {"id": 1}

app = Flask(__name__)
api = Api(app)
ns = Namespace("test")


@ns.route("/")
class TestResource(Resource):
    @accepts(
        dict(name="hey", type=str),
        dict(name="test", type=int, required=True, default=3),
        schema=HigherSchema,
        api=api,
    )
    def post(self):
        print(request.parsed_obj)
        print(request.parsed_args)
        return "Hello world"

    @accepts(
        dict(name="hey", type=str),
        dict(name="test", type=int, required=True, default=3),
        api=api,
    )
    def get(self):
        print(request.parsed_args)
        return "Hello world"

    @accepts(schema=HigherSchema, api=api)
    def put(self):
        print(request.parsed_obj)
        print(request.parsed_args)
        return "Hello world"


api.add_namespace(ns)

if __name__ == "__main__":
    app.run(debug=True)
