from setuptools import setup

setup(
    name="personalsite",
    packages=["personalsite"],
    include_package_data=True,
    install_requires=[
        "flask",
        "flask-sqlalchemy",
        "flask-markdown",
    ],
)
