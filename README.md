#	flask_accepts
I love `reqparse` from `Flask-RESTful` for input validation, but I got sick of writing code like this in every endpoint:

```
parser = reqparse.RequestParser()
parser.add_argument(name='foo', type=int, help='An important foo')
parser.add_argument(name='baz')
args = parser.parse_args()
```

So I made `flask_accepts`, which allows you to decorate an endpoint with just the input parameter information and it will internally parse those arguments and attach the results to the Flask `request` object in `request.parsed_args`. It will also automatically add the Swagger integrations from `Flask-RESTplus` where possible without you have to explicitly add the `@api.expect` decorator. This includes supporting Swagger even if you provided a Marshmallow schema -- the type mapping is handled internally.

The core of the library are two decorators, `@accepts` and `@responds`. The `@accepts` decorators defines what parameters or schemas the endpoint accepts, returning errors if the inputs fail validation, and `@responds` defines what schema should be used to serialize the output. This makes it easy to create a serialization layer on your API outputs without having to write a lot of extra code.

Here is an example (first `pip install flask_accepts`)


```python
from flask import Flask, jsonify, request
from flask_accepts import accepts


def create_app(env=None):
    app = Flask(__name__)

    @app.errorhandler(400)
    def error(e):
        return jsonify(e.data), 400

    @app.route('/test')
    @accepts(dict(name='foo', type=int), api=api)
    def test():
        print('foo = ', request.parsed_args.get('foo'))
        return 'success'

    return app


app = create_app()

print('Example with valid int param foo=3')
with app.test_client() as cl:
    resp = cl.get('/test?foo=3')
    print('Status: ', resp.status_code)

print('\n==========\n')

print('Example with invalid int param foo="baz"')
with app.test_client() as cl:
    resp = cl.get('/test?foo=baz')
    print('Status: ', resp.status_code)
    print('Content: ', resp.get_json())
```

Output:

```
Example with valid int param foo=3
request.parsed_args =  {'foo': 3}
foo =  3
Status:  200

==========

Example with invalid int param foo="baz"
Status:  400
Content:  {'errors': {'foo': "invalid literal for int() with base 10: 'baz'"}, 'message': 'Input payload validation failed'}
```

## Usage with Marshmallow schemas

Both the `accepts` and `responds` decorators will accept a keyword argument `schemas` that
is a Marshmallow Schema. You also provide the `api` namespace that you would like the Swagger documentation to be attached to. Under-the-hood, `flask_accepts` will handle conversion of the provided Marshmallow schema to an equivalent Flask-RESTplus `api.Model`, giving you the powerful control of Marshmallow combined with the awesomness of Swagger.

For `accepts`, the schema will be used to parse the JSON body
of a request, and the result will be stored in the Flask request object at `request.parsed_obj`. Note that this input is the _class_ of the schema, not an object of it. The object creation is handled internally. You can use the `post_load` decorator to control exactly what object is returned when the `load` method of the schema is called. See [here](https://marshmallow.readthedocs.io/en/3.0/extending.html) for more information.

For `responds`, the schema will be used to dump the returned value from the decorated function. Note that this means you should return the _object_ you want to serialize. You need not interact directly with the schema in any way other than passing it in the decorator.

For both decorators, you can pass `many=True` to the decorator, which will pass that along to the schema.

The following example includes examples of both Flask-RESTplus style endpoints with a Resource class containing REST methods as well as a "vanilla" Flask endpoint, which is just a function.

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
    foo = fields.String(100)
    baz = fields.Integer()

    @post_load
    def make(self, kwargs):
        return Widget(**kwargs)


def create_app(env=None):
    from flask_restplus import Api, Namespace, Resource

    app = Flask(__name__)
    api = Api(app)

    @app.route("/simple/make_a_widget", methods=["POST"])
    @accepts(dict(name="some_arg", type=str), schema=WidgetSchema)
    @responds(schema=WidgetSchema)
    def post():
        from flask import jsonify

        return request.parsed_obj

    @api.route("/restplus/make_a_widget")
    class WidgetResource(Resource):
        @accepts("Widget", dict(name="some_arg", type=str), schema=WidgetSchema, api=api)
        @responds(schema=WidgetSchema, api=api)
        def post(self):
            from flask import jsonify

            return request.parsed_obj

    return app


app = create_app()
if __name__ == "__main__":
    app.run(debug=True)
```

## Automatic Swagger documentation

The `accepts` decorator will automatically enable Swagger by internally adding the `@api.expects` decorator. If you have provided positional arguments to `accepts`, this involves generating the corresponding `api.parser()` (which is a `reqparse.RequestParser` that includes the Swagger context). If you provide a Marshmallow Schema, an equivalent `api.model` is generated and passed to `@api.expect`. These two can be mixed-and-matched, and the documentation will update accordingly.

### Defining the model name

Under-the-hood, `flask_accepts` translates and combines the provided dictionaries and/or Marshmallow schema into a single `api.Model`. The name of this model can be set either as a positional string argument or via the keyword argument `model_name` to the `@accepts` decorator. See the above example for the "Widget" model. This could also be written with keyword arguments as:

```python
    @api.route("/restplus/make_a_widget")
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