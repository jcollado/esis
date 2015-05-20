#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""esis package configuration script."""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from esis import (
    __author__ as author,
    __email__ as author_email,
    __version__ as version,
)


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'SQLAlchemy',
    'elasticsearch',
    'python-dateutil',
    'python-magic',
    'six',
]

test_requirements = [
    'coverage',
    'mock',
    'nose',
]

setup(
    name='esis',
    version=version,
    description="Elastic Search Index & Search",
    long_description=readme + '\n\n' + history,
    author=author,
    author_email=author_email,
    url='https://github.com/jcollado/esis',
    packages=[
        'esis',
    ],
    package_dir={'esis':
                 'esis'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords='elastic search index sqlite',
    entry_points={
        'console_scripts': [
            'esis = esis.cli:main',
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
