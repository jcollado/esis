===============================
esis
===============================

.. image:: https://img.shields.io/pypi/v/esis.svg
    :target: https://pypi.python.org/pypi/esis

.. image:: https://readthedocs.org/projects/esis/badge/?version=latest
    :target: https://readthedocs.org/projects/esis/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/travis/jcollado/esis.svg
    :target: https://travis-ci.org/jcollado/esis

.. image:: https://coveralls.io/repos/jcollado/esis/badge.svg
   :target: https://coveralls.io/r/jcollado/esis


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
