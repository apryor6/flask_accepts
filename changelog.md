0.2.4:

- Begin tracking changes in changelog.md

  0.3.0:

- Support vanilla Flask endpoints by wrapping with `jsonify` inside of `responds` when the method is not a class method (i.e. it is not inside a Resource)

  0.4.0:

- Enable user to specify the model name with either a positional or keyword argument

  0.5.0:

- Validation errors now return a 400 properly instead of a 500
- Greatly improve test coverage

  0.6.0:

- Support providing model name as positional parameter to `responds`

  0.7.0:

- Fix a bug causing models from `responds` to appear in request instead of response docs
- Add `status_code` parameter to `responds`
- Implement default naming creation based upon schema name if no model name provided. This will use the class name of the schema, removing the trailing "Schema" if provided.
- Enable marshaling responses without providing a schema (only using reqparse)
- Implement `validate` parameter in `responds`
- Drop support for Flask-RESTful
- Implement nice default names if none provided

  0.7.1:

- Remove stale default value

  0.8.0:

- Implement support for passing a schema instance _or_ type to accepts and responds
- Deprecate `many` parameter in favor of passing special parameters to an instance of the schema where necessary

  0.9.0:

- Upgrade to marshmallow 3

  0.9.1

- Add tests for multiply nested List/Nested types
- Fix a bug where model_name was not properly passed to for_swagger

  0.9.2

- Fix a bug causing all models to have default names

  0.10.0

- Add a number of additional type supports

  0.10.1

- Map bool type to restful.inputs.boolean internally

  0.11.0

- Map default values from Marshmallow Schemas to the example parameter of the generated api.model

  0.11.1

- Fix a bug where excluded/only fields were not being handled properly in Swagger
