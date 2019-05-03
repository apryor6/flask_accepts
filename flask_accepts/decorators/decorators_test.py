from flask import request

from flask_accepts.decorators import accepts
from flask_accepts.test.fixtures import app, client  # noqa


def test_arguments_are_added_to_request(app):  # noqa
    @app.route('/test')
    @accepts(dict(name='foo', type=int, help='An important foo'))
    def test():
        assert request.parsed_args
        return 'success'
    with app.test_client() as cl:
        resp = cl.get('/test?foo=3')
        assert resp.status_code == 200


def test_dict_arguments_are_correctly_added(app):  # noqa
    @app.route('/test')
    @accepts(
        {'name': 'an_int', 'type': int, 'help': 'An important int'},
        {'name': 'a_bool', 'type': bool, 'help': 'An important bool'},
        {'name': 'a_str', 'type': str, 'help': 'An important str'}
    )
    def test():
        print('request.parsed_args = ', request.parsed_args)
        assert request.parsed_args.get('an_int') == 1
        assert request.parsed_args.get('a_bool')
        assert request.parsed_args.get('a_str') == 'faraday'
        return 'success'
    with app.test_client() as cl:
        resp = cl.get('/test?an_int=1&a_bool=1&a_str=faraday')
        assert resp.status_code == 200


def test_failure_when_required_arg_is_missing(app):  # noqa
    @app.route('/test')
    @accepts(dict(name='foo',
                  type=int,
                  required=True,
                  help='A required foo'))
    def test():
        print(request.parsed_args)
        return 'success'
    with app.test_client() as cl:
        resp = cl.get('/test')
        print(resp.data)
        assert resp.status_code == 400


def test_failure_when_arg_is_wrong_type(app):  # noqa
    @app.route('/test')
    @accepts(dict(name='foo',
                  type=int,
                  required=True,
                  help='A required foo'))
    def test():
        print(request.parsed_args)
        return 'success'
    with app.test_client() as cl:
        resp = cl.get('/test?foo=baz')
        print(resp.data)
        assert resp.status_code == 400
