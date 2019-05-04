from flask_marshmallow import Marshmallow
from marshmallow import post_load
from flask import Flask, jsonify, request
from flask_accepts import accepts

ma = Marshmallow()


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

    @app.route('/widget', methods=['POST'])
    @accepts(dict(name='arg', type=int), schema=WidgetSchema)
    def test():
        print(request.parsed_args)
        print(request.parsed_obj)
        return jsonify('success')

    return app


app = create_app()


print('\nExample with valid schema params')
with app.test_client() as cl:
    resp = cl.post('/widget', json={'foo': 'baz', 'baz': 123})
    print('Status: ', resp.status_code)
    print('Status: ', resp.get_json())

print('\nExample with valid query params')
with app.test_client() as cl:
    resp = cl.post('/widget?arg=3', json={'foo': 'baz', 'baz': 123})
    print('Status: ', resp.status_code)
    print('Status: ', resp.get_json())

print('\nExample with invalid query params')
with app.test_client() as cl:
    resp = cl.post('/widget?arg=foo', json={'foo': 'baz', 'baz': 123})
    print('Status: ', resp.status_code)
    print('Status: ', resp.get_json())


print('\nExample with invalid query params and invalid schema params')
with app.test_client() as cl:
    resp = cl.post('/widget?arg=foo', json={'foo': 'baz', 'baz': 'fe'})
    print('Status: ', resp.status_code)
    print('Status: ', resp.get_json())
