# Copyright Alan (AJ) Pryor, Jr. 2018

from setuptools import setup, find_packages

setup(
    name="flask_accepts",
    author='Reclaim Health',
    author_email="noreply@reclaim.health",
    version="1.0.5",
    description="Easy, opinionated Flask input/output handling with Flask-restx and Marshmallow",
    ext_modules=[],
    packages=find_packages(),
    install_requires=[
        "marshmallow>=4.0.0",
        "flask-restx>=1.3.2; python_version >= '3.8'",
        "werkzeug>=3,<4; python_version >= '3.8'",
    ],
)
