# Copyright Alan (AJ) Pryor, Jr. 2018

from setuptools import setup, find_packages

setup(
    name="flask_accepts",
    author='Alan "AJ" Pryor, Jr.',
    author_email="apryor6@gmail.com",
    version="1.0.0",
    description="Easy, opinionated Flask input/output handling with Flask-restx and Marshmallow",
    ext_modules=[],
    packages=find_packages(),
    install_requires=[
        "marshmallow>=3.17.0",
        "flask-restx==1.1.0; python_version < '3.8'",
        "flask-restx>=1.2.0; python_version >= '3.8'",
        "werkzeug>=2,<3; python_version < '3.8'",
        "werkzeug>=3,<4; python_version >= '3.8'",
    ],
)
