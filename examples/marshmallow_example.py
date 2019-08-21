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
        @accepts(dict(name="some_arg", type=str), schema=WidgetSchema, api=api)
        @responds("Widget", schema=WidgetSchema, api=api)
        def post(self):
            from flask import jsonify

            return request.parsed_obj

    return app


app = create_app()
if __name__ == "__main__":
    app.run(debug=True)
