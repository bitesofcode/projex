import os
from setuptools import setup, find_packages
import projex

setup(
    name = 'projex',
    version = projex.__version__,
    author = 'Eric Hulser',
    author_email = 'eric.hulser@gmail.com',
    maintainer = 'Eric Hulser',
    maintainer_email = 'eric.hulser@gmail.com',
    description = 'Library of useful Python methods.',
    license = 'LGPL',
    keywords = '',
    url = 'https://github.com/ProjexSoftware/projex',
    include_package_data=True,
    scripts = [os.path.join('projex', 'scripts', 'xbuild.py')],
    packages = find_packages(),
    long_description= 'Library of useful Python methods.',
)
