import os
from setuptools import setup, find_packages
import projex

here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.md')) as f:
        README = f.read()
except IOError:
    README = projex.__doc__

try:
    VERSION = projex.__version__
except AttributeError:
    VERSION = '1.0'

try:
    REQUIREMENTS = projex.__depends__
except AttributeError:
    REQUIREMENTS = []

setup(
    name = 'projex',
    version = VERSION,
    author = 'Projex Software',
    author_email = 'team@projexsoftware.com',
    maintainer = 'Projex Software',
    maintainer_email = 'team@projexsoftware.com',
    description = '''''',
    license = 'LGPL',
    keywords = '',
    url = '',
    include_package_data=True,
    scripts = [r'projex\scripts\xbuild.py'],
    packages = find_packages(),
    install_requires = REQUIREMENTS,
    tests_require = REQUIREMENTS,
    long_description= README,
    classifiers=[],
)