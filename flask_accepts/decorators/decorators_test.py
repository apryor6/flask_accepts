from flask import request
from flask_restx import Resource, Api
from marshmallow import Schema, fields
from werkzeug.datastructures import MultiDict

from flask_accepts.decorators import accepts, responds
from flask_accepts.decorators.decorators import _convert_multidict_values_to_schema
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


def test_arguments_are_added_to_request_with_Resource_and_schema_instance(
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
            schema=TestSchema(),
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


def test_bool_argument_have_correct_input(app, client):
    @app.route("/test")
    @accepts(dict(name="foo", type=bool, help="An important bool"))
    def test():
        assert request.parsed_args["foo"] == False
        return "success"

    with client as cl:
        resp = cl.get("/test?foo=false")
        assert resp.status_code == 200


def test_failure_when_bool_argument_is_incorrect(app, client):
    @app.route("/test")
    @accepts(dict(name="foo", type=bool, help="An important bool"))
    def test():
        pass  # pragma: no cover

    with client as cl:
        resp = cl.get("/test?foo=falsee")
        assert resp.status_code == 400


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


def test_accepts_with_query_params_schema_single_value(app, client):  # noqa
    class TestSchema(Schema):
        foo = fields.Integer(required=True)

    @app.route("/test")
    @accepts("TestSchema", query_params_schema=TestSchema)
    def test():
        assert request.parsed_query_params["foo"] == 3
        return "success"

    with client as cl:
        resp = cl.get("/test?foo=3")
        assert resp.status_code == 200


def test_accepts_with_query_params_schema_list_value(app, client):  # noqa
    class TestSchema(Schema):
        foo = fields.List(fields.String(), required=True)

    @app.route("/test")
    @accepts("TestSchema", query_params_schema=TestSchema)
    def test():
        assert request.parsed_query_params["foo"] == ["3"]
        return "success"

    with client as cl:
        resp = cl.get("/test?foo=3")
        assert resp.status_code == 200


def test_accepts_with_query_params_schema_unknown_arguments(app, client):  # noqa
    class TestSchema(Schema):
        foo = fields.Integer(required=True)

    @app.route("/test")
    @accepts("TestSchema", query_params_schema=TestSchema)
    def test():
        # Extra query params should be excluded.
        assert "bar" not in request.parsed_query_params
        assert request.parsed_query_params["foo"] == 3
        return "success"

    with client as cl:
        resp = cl.get("/test?foo=3&bar=4")
        assert resp.status_code == 200


def test_failure_when_query_params_schema_arg_is_missing(app, client):  # noqa
    class TestSchema(Schema):
        foo = fields.String(required=True)

    @app.route("/test")
    @accepts("TestSchema", query_params_schema=TestSchema)
    def test():
        pass  # pragma: no cover

    with client as cl:
        resp = cl.get("/test")
        assert resp.status_code == 400


def test_failure_when_query_params_schema_arg_is_wrong_type(app, client):  # noqa
    class TestSchema(Schema):
        foo = fields.Integer(required=True)

    @app.route("/test")
    @accepts("TestSchema", query_params_schema=TestSchema)
    def test():
        pass  # pragma: no cover

    with client as cl:
        resp = cl.get("/test?foo=baz")
        assert resp.status_code == 400


def test_accepts_with_header_schema_single_value(app, client):  # noqa
    class TestSchema(Schema):
        Foo = fields.Integer(required=True)

    @app.route("/test")
    @accepts(headers_schema=TestSchema)
    def test():
        assert request.parsed_headers["Foo"] == 3
        return "success"

    with client as cl:
        resp = cl.get("/test", headers={"Foo": "3"})
        assert resp.status_code == 200


def test_accepts_with_header_schema_list_value(app, client):  # noqa
    class TestSchema(Schema):
        Foo = fields.List(fields.String(), required=True)

    @app.route("/test")
    @accepts(headers_schema=TestSchema)
    def test():
        assert request.parsed_headers["Foo"] == ["3"]
        return "success"

    with client as cl:
        resp = cl.get("/test", headers={"Foo": "3"})
        assert resp.status_code == 200


def test_accepts_with_header_schema_unknown_arguments(app, client):  # noqa
    class TestSchema(Schema):
        Foo = fields.List(fields.String(), required=True)

    @app.route("/test")
    @accepts(headers_schema=TestSchema)
    def test():
        # Extra header values should be excluded.
        assert "Bar" not in request.parsed_headers
        assert request.parsed_headers["Foo"] == ["3"]
        return "success"

    with client as cl:
        resp = cl.get("/test", headers={"Foo": "3", "Bar": "4"})
        assert resp.status_code == 200


def test_failure_when_header_schema_arg_is_missing(app, client):  # noqa
    class TestSchema(Schema):
        Foo = fields.String(required=True)

    @app.route("/test")
    @accepts("TestSchema", headers_schema=TestSchema)
    def test():
        pass  # pragma: no cover

    with client as cl:
        resp = cl.get("/test")
        assert resp.status_code == 400


def test_failure_when_header_schema_arg_is_wrong_type(app, client):  # noqa
    class TestSchema(Schema):
        Foo = fields.Integer(required=True)

    @app.route("/test")
    @accepts("TestSchema", headers_schema=TestSchema)
    def test():
        pass  # pragma: no cover

    with client as cl:
        resp = cl.get("/test", headers={"Foo": "baz"})
        assert resp.status_code == 400


def test_accepts_with_postional_args_query_params_schema_and_header_schema(app, client):  # noqa
    class QueryParamsSchema(Schema):
        query_param = fields.List(fields.String(), required=True)

    class HeadersSchema(Schema):
        Header = fields.Integer(required=True)

    @app.route("/test")
    @accepts(
        dict(name="foo", type=int, help="An important foo"),
        query_params_schema=QueryParamsSchema,
        headers_schema=HeadersSchema)
    def test():
        assert request.parsed_args["foo"] == 3
        assert request.parsed_query_params["query_param"] == ["baz", "qux"]
        assert request.parsed_headers["Header"] == 3
        return "success"

    with client as cl:
        resp = cl.get("/test?foo=3&query_param=baz&query_param=qux", headers={"Header": "3"})
        assert resp.status_code == 200


def test_accept_schema_instance_respects_many(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @accepts(schema=TestSchema(many=True), api=api)
        def post(self):
            return request.parsed_obj

    with client as cl:
        resp = cl.post("/test", data='[{"_id": 42, "name": "Jon Snow"}]', content_type='application/json')
        obj = resp.json
        assert obj == [{"_id": 42, "name": "Jon Snow"}]


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
            "King",
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


def test_responds_respects_envelope(app, client):  # noqa
    class TestSchema(Schema):
        _id = fields.Integer()
        name = fields.String()

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @responds(schema=TestSchema, api=api, envelope='test-data')
        def get(self):
            from flask import make_response, Response

            obj = {"_id": 42, "name": "Jon Snow"}
            return obj

    with client as cl:
        resp = cl.get("/test")
        assert resp.status_code == 200
        assert resp.json == {'test-data': {'_id': 42, 'name': 'Jon Snow'}}

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
            assert request.parsed_obj["child"] == {"_id": 42, "name": "test name"}
            assert request.parsed_obj["name"] == "test host"
            return "success"

    with client as cl:
        resp = cl.post(
            "/test?foo=3",
            json={"name": "test host", "child": {"_id": 42, "name": "test name"}},
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
                "name": "test name",
            }
            assert request.parsed_obj["child"] == {
                "name": "test host",
                "child": {"_id": 42, "name": "test name"},
            }
            assert request.parsed_obj["name"] == "test host host"
            return "success"

    with client as cl:
        resp = cl.post(
            "/test?foo=3",
            json={
                "name": "test host host",
                "child": {
                    "name": "test host",
                    "child": {"_id": 42, "name": "test name"},
                },
            },
        )
        assert resp.status_code == 200


def test_responds_with_validate(app, client):  # noqa
    import pytest
    from flask import jsonify
    from werkzeug.exceptions import InternalServerError

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
    import pytest
    from flask import jsonify
    from werkzeug.exceptions import InternalServerError

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
