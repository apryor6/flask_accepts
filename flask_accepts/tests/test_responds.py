import json

from attr import dataclass
from flask import request, Response, jsonify
from flask_restx import Resource, Api
from marshmallow import Schema, fields
from werkzeug.exceptions import InternalServerError

from flask_accepts.decorators import accepts, responds
from flask_accepts.tests.fixtures import app, client  # noqa


def test_responds(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @responds(schema=TestSchema, api=api)
        def get(self):
            obj = {"_id": 42, "name": "Jon Snow"}
            return obj

    with client as cl:
        resp = cl.get("/test")
        obj = resp.json
        assert obj["_id"] == 42
        assert obj["name"] == "Jon Snow"


def test_respond_schema_instance(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @responds(schema=TestSchema(), api=api)
        def get(self):
            obj = {"_id": 42, "name": "Jon Snow"}
            return obj

    with client as cl:
        resp = cl.get("/test")
        obj = resp.json
        assert obj["_id"] == 42
        assert obj["name"] == "Jon Snow"


def test_respond_schema_instance_respects_exclude(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @responds(schema=TestSchema(exclude=("_id",)), api=api)
        def get(self):
            obj = {"_id": 42, "name": "Jon Snow"}
            return obj

    with client as cl:
        resp = cl.get("/test")
        obj = resp.json
        assert "_id" not in obj
        assert obj["name"] == "Jon Snow"


def test_respond_schema_respects_many(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @responds(schema=TestSchema, many=True, api=api)
        def get(self):
            obj = [{"_id": 42, "name": "Jon Snow"}]
            return obj

    with client as cl:
        resp = cl.get("/test")
        obj = resp.json
        assert obj == [{"_id": 42, "name": "Jon Snow"}]


def test_respond_schema_instance_respects_many(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @responds(schema=TestSchema(many=True), api=api)
        def get(self):
            obj = [{"_id": 42, "name": "Jon Snow"}]
            return obj

    with client as cl:
        resp = cl.get("/test")
        obj = resp.json
        assert obj == [{"_id": 42, "name": "Jon Snow"}]


def test_responds_regular_route(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    @app.route("/test", methods=["GET"])
    @responds(schema=TestSchema)
    def get():
        obj = {"_id": 42, "name": "Jon Snow"}
        return obj

    with client as cl:
        resp = cl.get("/test")
        obj = resp.json
        assert obj["_id"] == 42
        assert obj["name"] == "Jon Snow"


def test_responds_passes_raw_responses_through_untouched(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @responds(schema=TestSchema, api=api)
        def get(self):


            obj = {"_id": 42, "name": "Jon Snow"}
            return Response("A prebuild response that won't be serialised", 201)

    with client as cl:
        resp = cl.get("/test")
        assert resp.status_code == 201


def test_responds_with_parser(app, client):  # noqa

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @responds(
            "King",
            dict(name="_id", type=int),
            dict(name="name", type=str),
            dict(name="value", type=float),
            dict(name="status", choices=("alive", "dead")),
            dict(name="todos", action="append"),
            api=api,
        )
        def get(self):
            return {
                "_id": 42,
                "name": "Jon Snow",
                "value": 100.0,
                "status": "alive",
                "todos": ["one", "two"],
            }

    with client as cl:
        resp = cl.get("/test")
        assert resp.status_code == 200
        assert resp.json == {
            "_id": 42,
            "name": "Jon Snow",
            "value": 100.0,
            "status": "alive",
            "todos": ["one", "two"],
        }


def test_responds_respects_status_code(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @responds(schema=TestSchema, api=api, status_code=999)
        def get(self):
            obj = {"_id": 42, "name": "Jon Snow"}
            return obj

    with client as cl:
        resp = cl.get("/test")
        assert resp.status_code == 999

def test_responds_respects_custom_status_code(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @responds(schema=TestSchema, api=api, status_code=999)
        def get(self):
            obj = {"_id": 42, "name": "Jon Snow"}
            return obj, 888

    with client as cl:
        resp = cl.get("/test")
        assert resp.status_code == 888

def test_responds_respects_envelope(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @responds(schema=TestSchema, api=api, envelope='tests-data')
        def get(self):
            obj = {"_id": 42, "name": "Jon Snow"}
            return obj

    with client as cl:
        resp = cl.get("/test")
        assert resp.status_code == 200
        assert resp.json == {'tests-data': {'_id': 42, 'name': 'Jon Snow'}}


def test_responds_skips_none_false(app, client):
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @responds(schema=TestSchema, api=api)
        def get(self):
            return {"_id": 42, "name": None}

    with client as cl:
        resp = cl.get("/test")
        assert resp.status_code == 200
        assert resp.json == {'_id': 42, 'name': None}


def test_responds_with_nested_skips_none_true(app, client):
    class NestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    class TestSchema(Schema):
        name = fields.String()
        child = fields.Nested(NestSchema)

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @responds(schema=TestSchema, api=api, skip_none=True, many=True)
        def get(self):
            return [{"name": None, "child": {"_id": 42, "name": None}}]

    with client as cl:
        resp = cl.get("/test")
        assert resp.status_code == 200
        assert resp.json == [{"child": {'_id': 42}}]


def test_accepts_with_nested_schema(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    class HostSchema(Schema):
        name = fields.String()
        child = fields.Nested(TestSchema)

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @accepts(
            "Foo",
            dict(name="foo", type=int, help="An important foo"),
            schema=HostSchema,
            api=api,
        )
        def post(self):
            assert request.parsed_obj
            assert request.parsed_obj["child"] == {"_id": 42, "name": "tests name"}
            assert request.parsed_obj["name"] == "tests host"
            return "success"

    with client as cl:
        resp = cl.post(
            "/test?foo=3",
            json={"name": "tests host", "child": {"_id": 42, "name": "tests name"}},
        )
        assert resp.status_code == 200


def test_accepts_with_twice_nested_schema(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    class HostSchema(Schema):
        name = fields.String()
        child = fields.Nested(TestSchema)

    class HostHostSchema(Schema):
        name = fields.String()
        child = fields.Nested(HostSchema)

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @accepts(
            "Foo",
            dict(name="foo", type=int, help="An important foo"),
            schema=HostHostSchema,
            api=api,
        )
        def post(self):
            assert request.parsed_obj
            assert request.parsed_obj["child"]["child"] == {
                "_id": 42,
                "name": "tests name",
            }
            assert request.parsed_obj["child"] == {
                "name": "tests host",
                "child": {"_id": 42, "name": "tests name"},
            }
            assert request.parsed_obj["name"] == "tests host host"
            return "success"

    with client as cl:
        resp = cl.post(
            "/test?foo=3",
            json={
                "name": "tests host host",
                "child": {
                    "name": "tests host",
                    "child": {"_id": 42, "name": "tests name"},
                },
            },
        )
        assert resp.status_code == 200


def test_responds_with_validate(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer(required=True)
        name = fields.String(required=True)

    @app.errorhandler(InternalServerError)
    def payload_validation_failure(err):
        return jsonify({"message": "Server attempted to return invalid data"}), 500

    @app.route("/test")
    @responds(schema=TestSchema, validate=True)
    def get():
        obj = {"wrong_field": 42, "name": "Jon Snow"}
        return obj

    with app.test_client() as cl:
        resp = cl.get("/test")
        obj = resp.json
        assert resp.status_code == 500
        assert resp.json == {"message": "Server attempted to return invalid data"}


def test_responds_with_validate(app, client):  # noqa
    class TestDataObj:
        def __init__(self, wrong_field, name):
            self.wrong_field = wrong_field
            self.name = name

    class TestSchema(Schema):
        _id = fields.Integer(required=True)
        name = fields.String(required=True)

    @app.errorhandler(InternalServerError)
    def payload_validation_failure(err):
        return jsonify({"message": "Server attempted to return invalid data"}), 500

    @app.route("/test")
    @responds(schema=TestSchema, validate=True)
    def get():
        obj = {"wrong_field": 42, "name": "Jon Snow"}
        data = TestDataObj(**obj)
        return data

    with app.test_client() as cl:
        resp = cl.get("/test")
        obj = resp.json
        assert resp.status_code == 500
        assert resp.json == {"message": "Server attempted to return invalid data"}


def test_no_schema_generates_correct_swagger(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)
    route = "/test"

    @api.route(route)
    class TestResource(Resource):
        @responds(api=api, status_code=201, description="My description")
        def post(self):
            obj = [{"_id": 42, "name": "Jon Snow"}]
            return obj

    with client as cl:
        cl.post(route, data='[{"_id": 42, "name": "Jon Snow"}]', content_type='application/json')
        route_docs = api.__schema__["paths"][route]["post"]

        responses_docs = route_docs['responses']['201']

        assert responses_docs['description'] == "My description"


def test_swagger_respects_existing_response_docs(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)
    route = "/test"

    @api.route(route)
    class TestResource(Resource):
        @responds(schema=TestSchema(many=True), api=api, description="My description")
        @api.doc(responses={401: "Not Authorized", 404: "Not Found"})
        def get(self):
            return [{"_id": 42, "name": "Jon Snow"}]

    with client as cl:
        cl.get(route)
        route_docs = api.__schema__["paths"][route]["get"]
        assert route_docs["responses"]["200"]["description"] == "My description"
        assert route_docs["responses"]["401"]["description"] == "Not Authorized"
        assert route_docs["responses"]["404"]["description"] == "Not Found"

def test_responds_can_use_alt_schema(app, client):  # noqa
    class DefaultSchema(Schema):
        id = fields.Integer()
        name = fields.String()

    class ErrorSchema(Schema):
        code = fields.String()
        error = fields.String()

    class TokenSchema(Schema):
        access_token = fields.String()
        refresh_token = fields.String()

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        alt_schemas = {
            888: TokenSchema,
            666: ErrorSchema,
        }
        @responds(schema=DefaultSchema, api=api, alt_schemas=alt_schemas)
        def get(self):
            resp_code = int(request.args.get("code"))

            if resp_code == 888:
                resp = {"access_token": "test_access_token", "refresh_token": "test_refresh_token"}
            elif resp_code == 666:
                resp = {"code": "UNKNOWN", "error": "Unhandled Exception"}
            else:
                resp = {"id": 1234, "name": "Fred Smith"}

            return resp, resp_code

    with client as cl:
        # test alternate schema
        resp = cl.get("/test?code=666")
        assert resp.status_code == 666
        assert resp.json == {"code": "UNKNOWN", "error": "Unhandled Exception"}

        # test different alternate schema
        resp = cl.get("/test?code=888")
        assert resp.status_code == 888
        assert resp.json == {"access_token": "test_access_token", "refresh_token": "test_refresh_token"}

        # test fallback to default schema with status code passthrough
        resp = cl.get("/test?code=401")
        assert resp.status_code == 401
        assert resp.json == {"id": 1234, "name": "Fred Smith"}
