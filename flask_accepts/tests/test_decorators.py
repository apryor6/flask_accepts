from flask_restx import Resource, Api
from marshmallow import Schema, fields
from werkzeug.datastructures import MultiDict

from flask_accepts.decorators import accepts, responds
from flask_accepts.decorators.decorators import _convert_multidict_values_to_schema
from flask_accepts.tests.fixtures import app, client  # noqa


def test_schema_generates_correct_swagger(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)
    route = "/test"

    @api.route(route)
    class TestResource(Resource):
        @accepts(model_name="MyRequest", schema=TestSchema(many=False), api=api)
        @responds(model_name="MyResponse", schema=TestSchema(many=False), api=api, description="My description")
        def post(self):
            obj = {"_id": 42, "name": "Jon Snow"}
            return obj

    with client as cl:
        cl.post(route, data='{"_id": 42, "name": "Jon Snow"}', content_type='application/json')
        route_docs = api.__schema__["paths"][route]["post"]
        responses_docs = route_docs['responses']['200']

        assert responses_docs['description'] == "My description"
        assert responses_docs['schema'] == {'$ref': '#/definitions/MyResponse'}
        assert route_docs['parameters'][0]['schema'] == {'$ref': '#/definitions/MyRequest'}

def test_schema_generates_correct_swagger_for_many(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)
    route = "/test"

    @api.route(route)
    class TestResource(Resource):
        @accepts(schema=TestSchema(many=True), api=api)
        @responds(schema=TestSchema(many=True), api=api, description="My description")
        def post(self):
            obj = [{"_id": 42, "name": "Jon Snow"}]
            return obj

    with client as cl:
        resp = cl.post(route, data='[{"_id": 42, "name": "Jon Snow"}]', content_type='application/json')
        route_docs = api.__schema__["paths"][route]["post"]
        assert route_docs['responses']['200']['schema'] == {"type": "array", "items": {"$ref": "#/definitions/Test"}}
        assert route_docs['parameters'][0]['schema'] == {"type": "array", "items": {"$ref": "#/definitions/Test"}}

def test_multidict_single_values_interpreted_correctly(app, client):  # noqa
    class TestSchema(Schema):
        name = fields.String(required=True)

    multidict = MultiDict([("name", "value"), ("new_value", "still_here")])
    result = _convert_multidict_values_to_schema(multidict, TestSchema())

    # `name` should be left a single value
    assert result["name"] == "value"

    # `new_value` should *not* be removed here, even though it"s not in the
    # schema.
    assert result["new_value"] == "still_here"

    # Also makes sure that if multiple values are found in the multidict, then
    # only the first one is returned.
    multidict = MultiDict([
        ("name", "value"),
        ("name", "value2"),
    ])
    result = _convert_multidict_values_to_schema(multidict, TestSchema())
    assert result["name"] == "value"

def test_multidict_list_values_interpreted_correctly(app, client):  # noqa
    class TestSchema(Schema):
        name = fields.List(fields.String(), required=True)

    multidict = MultiDict([
        ("name", "value"),
        ("new_value", "still_here")
    ])
    result = _convert_multidict_values_to_schema(multidict, TestSchema())

    # `name` should be converted to a list.
    assert result["name"] == ["value"]

    # `new_value` should *not* be removed here, even though it"s not in the schema.
    assert result["new_value"] == "still_here"

    # Also makes sure handling a list with >1 values also works.
    multidict = MultiDict([
        ("name", "value"),
        ("name", "value2"),
    ])
    result = _convert_multidict_values_to_schema(multidict, TestSchema())
    assert result["name"] == ["value", "value2"]
