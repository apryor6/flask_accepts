#	flask_accepts
I love `reqparse` from `Flask-RESTful` for input validation, but I got sick of writing code like this in every endpoint:

```
parser = reqparse.RequestParser()
parser.add_argument(name='foo', type=int, help='An important foo')
parser.add_argument(name='baz')
args = parser.parse_args()
```

So I made `flask_accepts`, which allows you to decorate an endpoint with just the input parameter information and it will internally parse those arguments and attach the results to the Flask `request` object in `request.parsed_args`

Here is an example (first `pip install flask_accepts`)


```python
from flask import Flask, jsonify, request
from flask_accepts import accepts


def create_app(env=None):
    app = Flask(__name__)
    @app.route('/')
    def health():
        return jsonify('healthy')

    @app.errorhandler(400)
    def error(e):
        return jsonify(e.data), 400
    return app


app = create_app()


@app.route('/test')
@accepts(dict(name='foo', type=int))
def test():
    print('foo = ', request.parsed_args.get('foo'))
    return 'success'


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