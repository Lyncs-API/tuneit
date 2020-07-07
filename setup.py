from setuptools import find_packages, setup
from functools import reduce

requirements = [
    "dill",
    "dataclasses",
    "python-varname",
    "tabulate",
    "numpy",
]

extras = {"graph": ["graphviz",]}

extras["all"] = list(set(reduce(lambda a, b: a + b, extras.values())))

setup(
    name="tuneit",
    author="Simone Bacchio",
    author_email="s.bacchio@gmail.com",
    url="https://tuneit.readthedocs.io/en/latest",
    download_url="https://github.com/sbacchio/tuneit",
    version="0.0.2",
    packages=find_packages(),
    install_requires=requirements,
    extras_require=extras,
)
