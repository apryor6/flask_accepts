from marshmallow import Schema, fields as ma
from flask import Flask
from flask_restplus import Resource, Api, fields as fr

from .utils import unpack_list, unpack_nested


def test_unpack_list():
    app = Flask(__name__)
    api = Api(app)
    result = unpack_list(ma.List(ma.Integer()), api=api)

    assert result


def test_unpack_nested():
    app = Flask(__name__)
    api = Api(app)
    result = unpack_nested(ma.Nested(ma.Integer()), api=api)

    assert result
