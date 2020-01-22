from marshmallow import fields, Schema
from flask import request, Flask
from flask_restx import Api, Resource

from flask_accepts import accepts, responds


class WidgetSchema(Schema):
    id = fields.Integer()
    created_at = fields.DateTime(dump_only=True)
    foo = fields.String(load_only=True)
    baz = fields.Integer()


def create_app():
    app = Flask(__name__)
    api = Api(app)

    @api.route("/widget")
    class WidgetResource(Resource):
        @accepts(schema=WidgetSchema, api=api)
        @responds(schema=WidgetSchema, api=api)
        def post(self):
            # save data to a new record, and return ID
            return request.parsed_obj

    return app


app = create_app()
if __name__ == "__main__":
    app.run(debug=True)
