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

classifiers = [
    "Development Status :: 2 - Pre-Alpha",
    "Intended Audience :: Developers",
    "Intended Audience :: Education",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: BSD License",
    "Natural Language :: English",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.6",
]

setup(
    name="tuneit",
    author="Simone Bacchio",
    author_email="s.bacchio@gmail.com",
    url="https://tuneit.readthedocs.io/en/latest",
    download_url="https://github.com/sbacchio/tuneit",
    version="0.0.3",
    license='BSD',
    packages=find_packages(),
    install_requires=requirements,
    extras_require=extras,
    python_requires='>=3',
    description="Tune, benchmark and crosscheck calculations contructing a computational graph",
    long_description=str(open("README.md").read()),
    long_description_content_type="text/markdown",
    classifiers=classifiers,
)
