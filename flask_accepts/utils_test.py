from dataclasses import dataclass
from unittest.mock import MagicMock, patch
import pytest
from marshmallow import Schema, fields as ma
from flask import Flask
from flask_restplus import Resource, Api, fields as fr

# from .utils import unpack_list, unpack_nested
import flask_accepts.utils as utils


def test_unpack_list():
    app = Flask(__name__)
    api = Api(app)
    with patch("flask_accepts.utils.unpack_list", wraps=utils.unpack_list) as mock:
        result = utils.unpack_list(ma.List(ma.Integer()), api=api)

        assert isinstance(result, fr.List)
        assert mock.call_count == 1


def test_unpack_list_of_list():
    app = Flask(__name__)
    api = Api(app)
    with patch(
        "flask_accepts.utils.unpack_list", wraps=utils.unpack_list
    ) as mock, patch.dict("flask_accepts.utils.type_map", {ma.List: mock}):

        result = utils.unpack_list(ma.List(ma.List(ma.Integer())), api=api)

        assert isinstance(result, fr.List)
        assert mock.call_count == 2


def test_unpack_nested():
    app = Flask(__name__)
    api = Api(app)

    class IntegerSchema(Schema):
        my_int: ma.Integer()

    result = utils.unpack_nested(ma.Nested(IntegerSchema), api=api)

    assert result


def test_unpack_nested_self():
    app = Flask(__name__)
    api = Api(app)

    class IntegerSchema(Schema):
        my_int = ma.Integer()
        children = ma.Nested("self", exclude=["children"])

    schema = IntegerSchema()

    result = utils.unpack_nested(schema.fields.get("children"), api=api)

    assert type(result) == fr.Nested


def test_unpack_nested_self_many():
    app = Flask(__name__)
    api = Api(app)

    class IntegerSchema(Schema):
        my_int = ma.Integer()
        children = ma.Nested("self", exclude=["children"], many=True)

    schema = IntegerSchema()

    result = utils.unpack_nested(schema.fields.get("children"), api=api)

    assert type(result) == fr.List


def test_get_default_model_name():
    from .utils import get_default_model_name

    class TestSchema(Schema):
        pass

    result = get_default_model_name(TestSchema)

    expected = "Test"
    assert result == expected


def test_get_default_model_name_works_with_multiple_schema_in_name():
    from .utils import get_default_model_name

    class TestSchemaSchema(Schema):
        pass

    result = get_default_model_name(TestSchemaSchema)

    expected = "TestSchema"
    assert result == expected


def test_get_default_model_name_that_does_not_end_in_schema():
    from .utils import get_default_model_name

    class SomeOtherName(Schema):
        pass

    result = get_default_model_name(SomeOtherName)

    expected = "SomeOtherName"
    assert result == expected


def test_get_default_model_name_default_names():
    from .utils import get_default_model_name, num_default_models

    for model_num in range(5):
        result = get_default_model_name()
        expected = f"DefaultResponseModel_{model_num + num_default_models}"
        assert result == expected


def test__check_load_dump_only_on_dump():
    @dataclass
    class FakeField:
        load_only: bool
        dump_only: bool

    assert not utils._check_load_dump_only(
        FakeField(load_only=True, dump_only=False), "dump"
    )
    assert utils._check_load_dump_only(
        FakeField(load_only=False, dump_only=True), "dump"
    )


def test__check_load_dump_only_on_load():
    @dataclass
    class FakeField:
        load_only: bool
        dump_only: bool

    assert utils._check_load_dump_only(
        FakeField(load_only=True, dump_only=False), "load"
    )
    assert not utils._check_load_dump_only(
        FakeField(load_only=False, dump_only=True), "load"
    )


def test__check_load_dump_only_raises_on_invalid_operation():
    @dataclass
    class FakeField:
        load_only: bool
        dump_only: bool

    with pytest.raises(ValueError):
        utils._check_load_dump_only(
            FakeField(load_only=True, dump_only=False), "not an operation"
        )

