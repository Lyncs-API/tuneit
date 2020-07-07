from setuptools import find_packages, setup
from functools import reduce

requirements = [
    "dill",
    "python-varname",
    "tabulate",
    "numpy",
]

extras = {"graph": ["graphviz",]}

extras["all"] = list(set(reduce(lambda a, b: a + b, extras.values())))

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
