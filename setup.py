from setuptools import find_packages
from setuptools import setup

requirements = [
    "dill",
    "python-varname",
    "tabulate",
]

extras = {"graph": ["graphviz",]}

setup(
    name="tunable",
    author="Simone Bacchio",
    author_email="s.bacchio@gmail.com",
    url="https://tunable.readthedocs.io/en/latest",
    download_url="https://github.com/sbacchio/tunable",
    version="0.0.0",
    packages=find_packages(),
    install_requires=requirements,
    extras_require=extras,
)
