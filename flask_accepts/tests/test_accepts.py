from flask import jsonify, request
from flask_restx import Resource, Api
from marshmallow import Schema, fields
from werkzeug.exceptions import InternalServerError

from flask_accepts.decorators import accepts, responds
from flask_accepts.tests.fixtures import app, client  # noqa


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
            assert request.parsed_obj["name"] == "tests name"
            return "success"

    with client as cl:
        resp = cl.post("/test?foo=3", json={"_id": 42, "name": "tests name"})
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
            assert request.parsed_obj["name"] == "tests name"
            return "success"

    with client as cl:
        resp = cl.post("/test?foo=3", json={"_id": 42, "name": "tests name"})
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
            json={"_id": "this is not an integer and will error", "name": "tests name"},
        )
        assert resp.status_code == 400
        assert "Not a valid integer." in resp.json["errors"]["_id"]


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
            json={"_id": "this is not an integer and will error", "name": "tests name"},
        )

        assert resp.status_code == 400
        assert "Not a valid integer." in resp.json["errors"]["_id"]


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


def test_accepts_with_query_params_schema_data_key(app, client):  # noqa
    class TestSchema(Schema):
        foo = fields.Integer(required=False, data_key="fooExternal")

    @app.route("/test")
    @accepts("TestSchema", query_params_schema=TestSchema)
    def test():
        assert request.parsed_args["fooExternal"] == 3
        assert request.parsed_query_params["foo"] == 3
        return "success"

    with client as cl:
        resp = cl.get("/test?fooExternal=3")
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


def test_accepts_with_header_schema_data_key(app, client):  # noqa
    class TestSchema(Schema):
        Foo = fields.Integer(required=False, data_key="Foo-External")

    @app.route("/test")
    @accepts("TestSchema", headers_schema=TestSchema)
    def test():
        assert request.parsed_headers["Foo"] == 3
        assert request.parsed_args["Foo-External"] == 3
        return "success"

    with client as cl:
        resp = cl.get("/test", headers={"Foo-External": "3"})
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


def test_accepts_with_form_schema_single_value(app, client):  # noqa
    class TestSchema(Schema):
        foo = fields.Integer(required=True)

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @accepts("TestSchema", form_schema=TestSchema, api=api)
        def post(self):
            assert request.parsed_args["foo"] == 3
            return "success"

    with client as cl:
        resp = cl.post("/test", data={"foo": 3})
        assert resp.status_code == 200


def test_accepts_with_form_schema_list_value(app, client):  # noqa
    class TestSchema(Schema):
        foo = fields.List(fields.String(), required=True)

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @accepts("TestSchema", form_schema=TestSchema, api=api)
        def post(self):
            assert request.parsed_form["foo"] == ["3"]
            assert request.parsed_args["foo"] == ["3"]
            return "success"

    with client as cl:
        resp = cl.post("/test", data={"foo": 3})
        assert resp.status_code == 200


def test_accepts_with_form_schema_unknown_arguments(app, client):  # noqa
    class TestSchema(Schema):
        foo = fields.Integer(required=True)

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @accepts("TestSchema", form_schema=TestSchema, api=api)
        def post(self):
            # Extra query params should be excluded.
            assert "bar" not in request.parsed_form
            assert request.parsed_form["foo"] == 3
            assert "bar" not in request.parsed_args
            assert request.parsed_args["foo"] == 3
            return "success"

    with client as cl:
        resp = cl.post("/test", data={"foo": 3, "bar": 4})
        assert resp.status_code == 200


def test_accepts_with_form_schema_data_key(app, client):  # noqa
    class TestSchema(Schema):
        foo = fields.Integer(required=False, data_key="fooExternal")

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @accepts("TestSchema", form_schema=TestSchema, api=api)
        def post(self):
            assert request.parsed_args["fooExternal"] == 3
            assert request.parsed_form["foo"] == 3
            return "success"

    with client as cl:
        resp = cl.post("/test", data={"fooExternal": 3})
        assert resp.status_code == 200


def test_failure_when_form_schema_arg_is_missing(app, client):  # noqa
    class TestSchema(Schema):
        foo = fields.String(required=True)

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @accepts("TestSchema", form_schema=TestSchema, api=api)
        def post(self):
                pass  # pragma: no cover

    with client as cl:
        resp = cl.post("/test")
        assert resp.status_code == 400


def test_failure_when_form_schema_arg_is_wrong_type(app, client):  # noqa
    class TestSchema(Schema):
        foo = fields.Integer(required=True)

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @accepts("TestSchema", form_schema=TestSchema, api=api)
        def post(self):
            pass  # pragma: no cover

    with client as cl:
        resp = cl.post("/test", data={"foo": "baz"})
        assert resp.status_code == 400


def test_accepts_with_postional_args_query_params_schema_and_header_schema_and_form_schema(app, client):  # noqa
    class QueryParamsSchema(Schema):
        query_param = fields.List(fields.String(), required=True)

    class HeadersSchema(Schema):
        Header = fields.Integer(required=True)

    class FormSchema(Schema):
        form = fields.String(required=True)

    api = Api(app)

    @api.route("/test")
    class TestResource(Resource):
        @accepts(
            dict(name="foo", type=int, help="An important foo"),
            query_params_schema=QueryParamsSchema,
            headers_schema=HeadersSchema,
            form_schema=FormSchema,
            api=api)
        def post(self):
            assert request.parsed_args["foo"] == 3
            assert request.parsed_query_params["query_param"] == ["baz", "qux"]
            assert request.parsed_headers["Header"] == 3
            assert request.parsed_form["form"] == "value"
            return "success"

    with client as cl:
        resp = cl.post(
            "/test?foo=3&query_param=baz&query_param=qux",
            headers={"Header": "3"},
            data={"form": "value"})
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
