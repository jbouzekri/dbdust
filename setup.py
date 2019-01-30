import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read().strip()


setup(
    name="dbdust",
    version=read('VERSION'),
    author="3sLab",
    description="Backup database, store and clean archive",
    license="MIT",
    keywords="database, backup, mysql, mongo, influx, elasticsearch",
    url="http://github.com/3slab/dbdust",
    packages=find_packages(exclude=["*.test", "*.test.*", "test.*", "test"]),
    long_description=read('README.md'),
    extras_require={
        'test': ['pytest', 'flake8', 'mock']
    },
    classifiers=[
        # TODO
    ],
    entry_points='''
        [console_scripts]
        dbdust = dbdust.admin:run
    '''
)
