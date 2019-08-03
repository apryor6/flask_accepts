0.2.4:

- Begin tracking changes in changelog.md

0.3.0:

- Support vanilla Flask endpoints by wrapping with `jsonify` inside of `responds` when the method is not a class method (i.e. it is not inside a Resource)