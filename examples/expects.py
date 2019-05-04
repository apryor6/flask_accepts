```
curl http://localhost:5000/widget?bla=1
{
    "baz": 3,
    "foo": "test"
}
```

```
curl -d '{"foo":"hey", "baz": 1}' http://localhost:5000/widget?bla=1 -H 'Content-Type: application/json'
{
  "baz": 1, 
  "foo": "hey"
}
```

from flask_marshmallow import Marshmallow
from flask import Flask, jsonify, request
from flask_accepts import accepts, responds
from flask_restplus import Namespace, Api, Resource, fields
from marshmallow import post_load

api = Api(title='test', version='0.0.0', description='A test API')
ma = Marshmallow()


# def create_app(env=None):
#     app = Flask(__name__)

#     @app.errorhandler(400)
#     def error(e):
#         return jsonify(e.data), 400

#     widgets = Namespace('widgets', description='foo bar')
#     # @widgets.doc('A test api')
#     # @widgets.route('/widget', methods=['POST'])
#     @app.route('/widget', methods=['POST'])
#     # @accepts(schema=WidgetSchema)
#     def test():
#         print(request.parsed_obj)
#         return jsonify('success')
#     api.add_namespace(widgets, pref)
#     api.init_app(app)
#     return app


# app = create_app()
app = Flask(__name__)


@app.errorhandler(400)
def error(e):
    return jsonify(e.data), 400


ns = Namespace('ns', description='foo bar')
widgets = Namespace('', description='A bunch of widgets')
# @widgets.doc('A test api')


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


@widgets.route('/widget')
class WidgetResource(Resource):
    @accepts(dict(name='bla', type=int, required=True), schema=WidgetSchema)
    def post(self):
        print(request.parsed_obj)
        print(request.parsed_args)
        return jsonify(request.parsed_obj.__dict__)
        # return jsonify('success')

    @responds(schema=WidgetSchema)
    def get(self):
        # print(request.parsed_obj)
        # w = Widget(foo='test', baz=3)
        # return jsonify(WidgetSchema().dump(w).data)
        return Widget(foo='test', baz=3)


api.add_namespace(ns)
api.add_namespace(widgets)
api.init_app(app)
ma.init_app(app)

# print('Example with valid widget params')
# with app.test_client() as cl:
#     resp = cl.post('/widget?foo=baz', json={'foo': 'baz', 'baz': 123})
#     print('Status: ', resp.status_code)
#     print('Status: ', resp.get_json())

# # print('\n==========\n')

# # print('Example with invalid int param foo="baz"')
# # with app.test_client() as cl:
# #     resp = cl.get('/test?foo=baz')
# #     print('Status: ', resp.status_code)
# #     print('Content: ', resp.get_json())

if __name__ == '__main__':
    app.run(debug=True)
