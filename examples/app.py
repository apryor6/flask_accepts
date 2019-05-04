from flask import Flask, jsonify, request
from flask_accepts import accepts


# def create_app(env=None):
app = Flask(__name__)
app.config['BUNDLE_ERRORS'] = True


@app.errorhandler(400)
def error(e):
    return jsonify(e.data), 400


@app.route('/', methods=['GET'])
@accepts(dict(name='foo', type=int), dict(name='baz', type=float))
def test():
    return jsonify(request.parsed_args)


with app.test_client() as cl:
    resp = cl.get('/test?foo=3')
    print('Status: ', resp.status_code)
    print('Return: ', resp.get_json())
print('\n==========\n')

print('Example with invalid int param foo="baz"')
with app.test_client() as cl:
    resp = cl.get('/test?foo=baz', headers={'Content-Type': 'appliation/json'})
    print('Status: ', resp.status_code)
    print('Return: ', resp.get_json())


if __name__ == '__main__':
    app.run(debug=True)
