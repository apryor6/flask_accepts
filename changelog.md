0.2.4:

- Begin tracking changes in changelog.md

0.3.0:

- Support vanilla Flask endpoints by wrapping with `jsonify` inside of `responds` when the method is not a class method (i.e. it is not inside a Resource)

0.4.0:

- Enable user to specify the model name with either a positional or keyword argument