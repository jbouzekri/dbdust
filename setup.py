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
    url="https://github.com/3slab/dbdust",
    packages=find_packages(exclude=["*.test", "*.test.*", "test.*", "test"]),
    long_description=read('README.md'),
    install_requires=('azure-storage-blob',),
    extras_require={
        'test': ['pytest', 'flake8']
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: System :: Archiving :: Backup'
    ],
    entry_points='''
        [console_scripts]
        dbdust = dbdust.admin:run
    '''
)
