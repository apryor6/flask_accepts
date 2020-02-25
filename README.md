[![codecov](https://codecov.io/gh/apryor6/flask_accepts/branch/master/graph/badge.svg)](https://codecov.io/gh/apryor6/flask_accepts)
[![license](https://img.shields.io/github/license/apryor6/flask_accepts)](https://img.shields.io/github/license/apryor6/flask_accepts)
[![code_style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://img.shields.io/badge/code%20style-black-000000.svg)

---

- [flask_accepts](#flask-accepts)
  - [Installation](#installation)
  - [Basic usage](#basic-usage)
  - [Usage with "vanilla Flask"](#usage-with--vanilla-flask-)
  * [Usage with Marshmallow schemas](#usage-with-marshmallow-schemas)
    - [Marshmallow validators](#marshmallow-validators)
    - [Default values](#default-values)
  * [Automatic Swagger documentation](#automatic-swagger-documentation)
    - [Defining the model name](#defining-the-model-name)
    - [Error handling](#error-handling)
    - [Specifying response codes](#specifying-response-codes)
- [Development setup](#development-setup)

---

# flask_accepts

I love `reqparse` from `Flask-restx` for input validation, but I found it hard to keep all of the different decorators and what they do straight, and I got sick of writing code like this in every endpoint:

```
parser = reqparse.RequestParser()
parser.add_argument(name='foo', type=int, help='An important foo')
parser.add_argument(name='baz')
args = parser.parse_args()
```

And I also love Marshmallow, but the two technologies don't really play well together, at least not out-of-the-box.

So I made `flask_accepts`, which gives you two simple decorators, `accepts` and `responds`, that combine these two libraries in a way that's easy-to-use for input/output handling in Flask. The `@accepts` decorators defines what parameters or schemas the endpoint accepts, returning errors if the inputs fail validation, and `@responds` defines how to serialize the output, supporting both `reqparse` models and `Marshmallow` schemas.

This makes it easy to create a serialization layer on your API outputs without having to write a lot of extra code while allowing usage of restx and Marshmallow side-by-side. It will also automatically add the Swagger integrations from `Flask-restx` where possible without you have to explicitly add the various restx decorators (it does that for you). _This includes supporting Swagger even if you provided a Marshmallow schema -- the type mapping is handled internally._

`accepts` takes input parameter information and internally parses those arguments and attaches the results to the Flask `request` object in `request.parsed_args`

`responds` takes the provided model parameters or schema and uses that to serialize the output of the decorated function.

### Installation

Simple, `pip install flask_accepts`

Note, running the example code from the source directory will require Python 3.7 or greater as these leverage dataclasses.

### Basic usage

Here is a basic example of an endpoint that takes a couple of URL query params and returns a new Widget. The `accepts` and `responds` decorators both take as positional arguments any number of dictionaries that will be passed to `flask_restful.reqparse.ArgumentParser` (see [here](https://flask-restx.readthedocs.io/en/stable/parsing.html)). A Marshmallow schema may be passed with the `schema` parameter. These different arguments can be mixed as you see fit.

```python
from dataclasses import dataclass
from marshmallow import Schema, fields, post_load
from flask import Flask, request
from flask_accepts import accepts, responds
from flask_restx import Api, Resource


@dataclass
class Widget:
    foo: str
    baz: int


class WidgetSchema(Schema):
    foo = fields.String()
    baz = fields.Integer()


def create_app():
    app = Flask(__name__)
    api = Api(app)

    @api.route("/widget")
    class WidgetResource(Resource):
        @accepts(dict(name="foo", type=str), dict(name="baz", type=int), api=api)
        @responds(schema=WidgetSchema, api=api)
        def get(self):
            return Widget(**request.parsed_args)

    return app


if __name__ == "__main__":
    create_app().run()
```

### Usage with "vanilla Flask"

Here is a basic example of an endpoint that makes and returns a new Widget

```python
from flask import Flask, request
from flask_accepts import accepts, responds

from .widget import Widget, WidgetSchema, make_widget


def create_app():
    app = Flask(__name__)

    @app.route("/widget")
    @accepts(dict(name="foo", type=str))
    @responds(schema=WidgetSchema)
    def widget():
        name: str = request.parsed_args["foo"]
        widget: Widget = make_widget(name)
        return widget

    return app
```

## Usage with Marshmallow schemas

Both the `accepts` and `responds` decorators will accept a keyword argument `schemas` that
is a Marshmallow Schema. You also provide the `api` namespace that you would like the Swagger documentation to be attached to. Under-the-hood, `flask_accepts` will handle conversion of the provided Marshmallow schema to an equivalent Flask-restx `api.Model`, giving you the powerful control of Marshmallow combined with the awesomness of Swagger.

For `accepts`, the schema will be used to parse the JSON body
of a request, and the result will be stored in the Flask request object at `request.parsed_obj`. Note that this input is the _class_ of the schema, not an object of it. The object creation is handled internally. You can use the `post_load` decorator to control exactly what object is returned when the `load` method of the schema is called. See [here](https://marshmallow.readthedocs.io/en/3.0/extending.html) for more information.

For `responds`, the schema will be used to dump the returned value from the decorated function. Note that this means you should return the _object_ you want to serialize. You need not interact directly with the schema in any way other than passing it in the decorator.

For both decorators, you can pass a schema instance, which allows you to pass additional parameters such as `many=True`

The following example includes examples of both Flask-restx style endpoints with a Resource class containing REST methods as well as a "vanilla" Flask endpoint, which is just a function.

```python
from dataclasses import dataclass
from marshmallow import fields, Schema, post_load
from flask import Flask, jsonify, request
from flask_accepts import accepts, responds


@dataclass
class Widget:
    foo: str
    baz: int


class WidgetSchema(Schema):
    foo = fields.String()
    baz = fields.Integer()

    @post_load
    def make(self, data, **kwargs):
        return Widget(**data)


def create_app(env=None):
    from flask_restx import Api, Namespace, Resource

    app = Flask(__name__)
    api = Api(app)

    @app.route("/simple/make_a_widget", methods=["POST"])
    @accepts(dict(name="some_arg", type=str), schema=WidgetSchema)
    @responds(schema=WidgetSchema)
    def post():
        from flask import jsonify

        return request.parsed_obj

    @api.route("/restx/make_a_widget")
    class WidgetResource(Resource):
        @accepts(dict(name="some_arg", type=str), schema=WidgetSchema, api=api)
        @responds(schema=WidgetSchema, api=api)
        def post(self):
            from flask import jsonify

            return request.parsed_obj

    return app


app = create_app()
if __name__ == "__main__":
    app.run(debug=True)
```

#### Marshmallow validators

You can provide any of the built-in validators to Marshmallow schemas. See [here](https://github.com/apryor6/flask_accepts/blob/master/examples/marshmallow_validator_example.py) for an example of using schemas + validators inside of flask_accepts.

#### Default values

Default values provided to Marshmallow schemas will be internally mapped and displayed in the Swagger documentation. See [this example](https://github.com/apryor6/flask_accepts/blob/master/examples/default_values.py) for a usage of `flask_accepts` with nested Marshmallow schemas and default values that will display correctly in Swagger.

## Automatic Swagger documentation

The `accepts` decorator will automatically enable Swagger by internally adding the `@api.expects` decorator. If you have provided positional arguments to `accepts`, this involves generating the corresponding `api.parser()` (which is a `reqparse.RequestParser` that includes the Swagger context). If you provide a Marshmallow Schema, an equivalent `api.model` is generated and passed to `@api.expect`. These two can be mixed-and-matched, and the documentation will update accordingly.

### Defining the model name

Under-the-hood, `flask_accepts` translates and combines the provided dictionaries and/or Marshmallow schema into a single `api.Model`. The name of this model can be set either as a positional string argument or via the keyword argument `model_name` to the `@accepts` decorator.

```python

@api.route("/restx/make_a_widget")
class WidgetResource(Resource):
    @accepts(
        "Widget",
        dict(name="some_arg", type=str),
        schema=WidgetSchema,
        api=api,
    )
    @responds(schema=WidgetSchema, api=api)
    def post(self):
        from flask import jsonify
        return request.parsed_obj
```

This could also be written with keyword arguments as:

```python
@api.route("/restx/make_a_widget")
class WidgetResource(Resource):
    @accepts(
        dict(name="some_arg", type=str),
        model_name="Widget",
        schema=WidgetSchema,
        api=api,
    )
    @responds(schema=WidgetSchema, api=api)
    def post(self):
        from flask import jsonify

        return request.parsed_obj
```

### Error handling

`flask_accepts` will unify/bundle errors for the underlying reqparse and/or Marshmallow schema errors into a single 400 response upon validation errors. The payload contains an "errors" object with one key for each parameter that was not valid with the value of that key being the error message. There is one special key, `schema_errors` that will contain the nested output of the errors for schema validation with Marshmallow. Here is an example of a full error object followed by a test that produced this output.

```json
{
  "errors": {
    "foo": "An important foo invalid literal for int() with base 10: 'not_int'",
    "schema_errors": { "_id": ["Not a valid integer."] }
  },
  "message": "Input payload validation failed"
}
```

```python
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
```

### Specifying response codes

The response code can be specified in the `responds` decorator through the `status_code` parameter.

```python
from marshmallow import fields, Schema, post_load
from flask import Flask, jsonify, request
from flask_accepts import accepts, responds


class Widget:
    def __init__(self, foo: str, baz: int):
        self.foo = foo
        self.baz = baz

    def __repr__(self):
        return f"<Widget(foo='{self.foo}', baz={self.baz})>"


class WidgetSchema(Schema):
    foo = fields.String()
    baz = fields.Integer()

    @post_load
    def make(self, data, **kwargs):
        return Widget(**data)


def create_app(env=None):
    from flask_restx import Api, Namespace, Resource

    app = Flask(__name__)
    api = Api(app)

    @app.route("/simple/make_a_widget", methods=["POST"])
    @accepts(dict(name="some_arg", type=str), schema=WidgetSchema)
    @responds(schema=WidgetSchema, status_code=201)
    def post():
        from flask import jsonify

        return request.parsed_obj

    @api.route("/restx/make_a_widget")
    class WidgetResource(Resource):
        @accepts("Widget", dict(name="some_arg", type=str), schema=WidgetSchema, api=api)
        @responds(schema=WidgetSchema, api=api, status_code=201)
        def post(self):
            from flask import jsonify

            return request.parsed_obj

    return app


app = create_app()
if __name__ == "__main__":
    app.run(debug=True)
```

# Development setup

To install _flask_accepts_ for development, fork or clone the repository, create virtual environment
and while active install dev requirements.

    (venv) [user@station flask_accepts]$ pip install -r dev-requirements.txt

Plesae follow contribution [guidelines](https://opensource.guide/how-to-contribute/), add comments and document your changes before providing a pull request.
