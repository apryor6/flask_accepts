#	flask_accepts
I love `reqparse` from `Flask-RESTful` for input validation, but I got sick of writing code like this in every endpoint:

```
parser = reqparse.RequestParser()
parser.add_argument(name='foo', type=int, help='An important foo')
parser.add_argument(name='baz')
args = parser.parse_args()
```

So I made `flask_accepts`, which allows you to decorate an endpoint with just the input parameter information and it will internally parse those arguments and attach the results to the Flask `request` object in `request.parsed_args`. It will also automatically add the Swagger integrations from `Flask-RESTplus` where possible without you have to explicitly add the `@api.expect` decorator. This includes supporting Swagger even if you provided a Marshmallow schema -- the type mapping is handled internally.

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
foo =  3
Status:  200

==========

Example with invalid int param foo="baz"
Status:  400
Content:  {'message': {'foo': "invalid literal for int() with base 10: 'baz'"}}
```

## Usage with Marshmallow schemas

Both the `accepts` and `responds` decorators will accept a keyword argument `schemas` that
is a Marshmallow Schema. You also provide the `api` namespace that you would like the Swagger documentation to be attached to. Under-the-hood, `flask_accepts` will handle conversion of the provided Marshmallow schema to an equivalent Flask-RESTplus `api.Model`, giving you the powerful control of Marshmallow combined with the awesomness of Swagger.

For `accepts`, the schema will be used to parse the JSON body
of a request, and the result will be stored in the Flask request object at `request.parsed_obj`. Note that this input is the _class_ of the schema, not an object of it. The object creation is handled internally. You can use the `post_load` decorator to control exactly what object is returned when the `load` method of the schema is called. See [here](https://marshmallow.readthedocs.io/en/3.0/extending.html) for more information.

For `responds`, the schema will be used to dump the returned value from the decorated function. Note that this means you should return the _object_ you want to serialize. You need not interact directly with the schema in any way other than passing it in the decorator.

For both decorators, you can pass `many=True` to the decorator, which will pass that
along to the schema.

```python
class Widget:
    def __init__(self, foo: str, baz: int):
        self.foo = foo
        self.baz = baz

    def __repr__(self):
        return f"<Widget(foo='{self.foo}', baz={self.baz})>"


class WidgetSchema(ma.Schema):
    foo = ma.String(100)
    baz = ma.Integer()

    @post_load
    def make(self, kwargs):
        return Widget(**kwargs)


def create_app(env=None):
    app = Flask(__name__)
    ma.init_app(app)
    @app.errorhandler(400)
    def error(e):
        return jsonify(e.data), 400

    @app.route('/get_a_widget', methods=['GET'])
    @responds(schema=WidgetSchema)
    def get():
        return request.parsed_obj

    @app.route('/make_a_widget', methods=['POST'])
    @accepts(dict(name='arg', type=int), schema=WidgetSchema, api=api)
    def post():
        print(request.parsed_args)
        print(request.parsed_obj)
        return jsonify('success')

    return app
```

## Automatic Swagger documentation

The `accepts` decorator will automatically enable Swagger by internally adding the `@api.expects` decorator. If you have provided positional arguments to `accepts`, this involves generating the corresponding `api.parser()` (which is a `reqparse.RequestParser` that includes the Swagger context). If you provide a Marshmallow Schema, an equivalent `api.model` is generated and passed to `@api.expect`. These two can be mixed-and-matched, and the documentation will update accordingly.