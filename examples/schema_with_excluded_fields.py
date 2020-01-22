from marshmallow import fields, Schema
from flask import request, Flask
from flask_restx import Api, Resource

from flask_accepts import accepts, responds


class WidgetSchema(Schema):
    id = fields.Integer()
    created_at = fields.DateTime()
    foo = fields.String()
    baz = fields.Integer()


def create_app():
    app = Flask(__name__)
    api = Api(app)

    @api.route("/widget")
    class WidgetResource(Resource):
        @accepts("WidgetCreate", schema=WidgetSchema(only=["foo", "baz"]), api=api)
        @responds(schema=WidgetSchema, api=api)
        def post(self):
            # save data to a new record, and return ID
            return request.parsed_obj

        @accepts(dict(name="id", type=int), schema=WidgetSchema, api=api)
        @responds(schema=WidgetSchema(exclude=["created_at"]), api=api)
        def patch(self):
            return request.parsed_obj

    return app


app = create_app()
if __name__ == "__main__":
    app.run(debug=True)
