"Usage: python -m get_version ./setup.py"

import setuptools
import sys

setuptools.setup = lambda *args, version=None, **kwargs: print(version)

exec(open(sys.argv[1]).read())
