===============================
esis
===============================

.. image:: https://img.shields.io/pypi/v/esis.svg
    :target: https://pypi.python.org/pypi/esis

.. image:: https://readthedocs.org/projects/esis/badge/?version=latest
    :target: https://readthedocs.org/projects/esis/?badge=latest
    :alt: Documentation Status

.. image:: https://requires.io/github/jcollado/esis/requirements.svg?branch=master
    :target: https://requires.io/github/jcollado/esis/requirements/?branch=master
    :alt: Requirements Status

.. image:: https://landscape.io/github/jcollado/esis/master/landscape.svg?style=flat
   :target: https://landscape.io/github/jcollado/esis/master
   :alt: Code Health

.. image:: https://img.shields.io/travis/jcollado/esis.svg
    :target: https://travis-ci.org/jcollado/esis

.. image:: https://coveralls.io/repos/jcollado/esis/badge.svg
    :target: https://coveralls.io/r/jcollado/esis

.. image:: https://badge.waffle.io/jcollado/esis.svg?label=ready&title=Ready
    :target: https://waffle.io/jcollado/esis
    :alt: 'Stories in Ready'

.. image:: https://badges.gitter.im/Join%20Chat.svg
    :alt: Join the chat at https://gitter.im/jcollado/esis
    :target: https://gitter.im/jcollado/esis?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge


Elasticsearch Index & Search

* Free software: MIT license
* Documentation: https://esis.readthedocs.org.

Features
--------

* Index content for every SQLite database row in Elasticsearch
* Search indexed content

Usage
-----

* Index every SQLite database row under a given directory (recursively)

.. code-block:: bash

    esis index <directory>


* Search for a given string in the indexed data

.. code-block:: bash

    esis search <query>

* Get information about the number of indexed documents

.. code-block:: bash

    esis count

* Delete all indexed documents

.. code-block:: bash

    esis clean
