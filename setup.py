#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'SQLAlchemy',
    'python-dateutil',
    'python-magic',
    'elasticsearch',
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='esis',
    version='0.1.0',
    description="Elastic Search Index & Search",
    long_description=readme + '\n\n' + history,
    author="Javier Collado",
    author_email='jcollado@nowsecure.com',
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
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
