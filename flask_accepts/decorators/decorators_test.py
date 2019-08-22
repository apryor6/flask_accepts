from flask import request
from flask_restplus import Resource, Api
from marshmallow import Schema, fields

from flask_accepts.decorators import accepts, responds
from flask_accepts.test.fixtures import app, client  # noqa


def test_arguments_are_added_to_request(app, client):  # noqa
    @app.route("/test")
    @accepts("Foo", dict(name="foo", type=int, help="An important foo"))
    def test():
        assert request.parsed_args
        return "success"

    with client as cl:
        resp = cl.get("/test?foo=3")
        assert resp.status_code == 200


def test_arguments_are_added_to_request_with_Resource(app, client):  # noqa
    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @accepts("Foo", dict(name="foo", type=int, help="An important foo"), api=api)
        def get(self):
            assert request.parsed_args
            return "success"

    with client as cl:
        resp = cl.get("/test?foo=3")
        assert resp.status_code == 200


def test_arguments_are_added_to_request_with_Resource_and_schema(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @accepts(
            "Foo",
            dict(name="foo", type=int, help="An important foo"),
            schema=TestSchema,
            api=api,
        )
        def post(self):
            assert request.parsed_obj
            assert request.parsed_obj["_id"] == 42
            assert request.parsed_obj["name"] == "test name"
            return "success"

    with client as cl:
        resp = cl.post("/test?foo=3", json={"_id": 42, "name": "test name"})
        assert resp.status_code == 200


def test_validation_errors_added_to_request_with_Resource_and_schema(
    app, client
):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @accepts(
            "Foo",
            dict(name="foo", type=int, help="An important foo"),
            schema=TestSchema,
            api=api,
        )
        def post(self):
            pass  # pragma: no cover

    with client as cl:
        resp = cl.post(
            "/test?foo=3",
            json={"_id": "this is not an integer and will error", "name": "test name"},
        )
        assert resp.status_code == 400
        assert "Not a valid integer." in resp.json["schema_errors"]["_id"]


def test_validation_errors_from_all_added_to_request_with_Resource_and_schema(
    app, client
):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @accepts(
            "Foo",
            dict(name="foo", type=int, help="An important foo"),
            dict(name="foo2", type=int, help="An important foo2"),
            schema=TestSchema,
            api=api,
        )
        def post(self):
            pass  # pragma: no cover

    with client as cl:
        resp = cl.post(
            "/test?foo=not_int",
            json={"_id": "this is not an integer and will error", "name": "test name"},
        )

        assert resp.status_code == 400
        assert "Not a valid integer." in resp.json["errors"]["schema_errors"]["_id"]


def test_dict_arguments_are_correctly_added(app, client):  # noqa
    @app.route("/test")
    @accepts(
        {"name": "an_int", "type": int, "help": "An important int"},
        {"name": "a_bool", "type": bool, "help": "An important bool"},
        {"name": "a_str", "type": str, "help": "An important str"},
    )
    def test():
        assert request.parsed_args.get("an_int") == 1
        assert request.parsed_args.get("a_bool")
        assert request.parsed_args.get("a_str") == "faraday"
        return "success"

    with client as cl:
        resp = cl.get("/test?an_int=1&a_bool=1&a_str=faraday")
        assert resp.status_code == 200


def test_failure_when_required_arg_is_missing(app, client):  # noqa
    @app.route("/test")
    @accepts(dict(name="foo", type=int, required=True, help="A required foo"))
    def test():
        pass  # pragma: no cover

    with client as cl:
        resp = cl.get("/test")
        assert resp.status_code == 400


def test_failure_when_arg_is_wrong_type(app, client):  # noqa
    @app.route("/test")
    @accepts(dict(name="foo", type=int, required=True, help="A required foo"))
    def test():
        pass  # pragma: no cover

    with client as cl:
        resp = cl.get("/test?foo=baz")
        assert resp.status_code == 400


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
            from flask import make_response, Response

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
            dict(name="_id", type=int),
            dict(name="name", type=str),
            dict(name="value", type=float),
            dict(name="status", choices=("alive", "dead")),
            dict(name="todos", action="append"),
            api=api,
        )
        def get(self):
            from flask import make_response, Response

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
            from flask import make_response, Response

            obj = {"_id": 42, "name": "Jon Snow"}
            return obj

    with client as cl:
        resp = cl.get("/test")
        assert resp.status_code == 999

