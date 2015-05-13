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


Docker containers
-----------------

Docker files are included in the source code to run esis and elasticsearch in
their own containers. To build/pull the images needed to run esis and start the
elasticsearch server, use the following commands:

.. code-block:: bash

    docker-compose build
    docker-compose start

After that, to launch esis in a container run:

.. code-block:: bash

    docker-compose run esis <subcommand>

where *<subcommand>* is any of the subcommands in the previous section
(*index*, *search*, *count* or *clean*).

Note:

* If *docker-compose run* is executed too quickly, then a connection error
  might be returning meaning that elasticsearch is still initializing.

* The entry point in the esis container uses the *--host* command line option
  to connect to the linked container where elasticsearch is running.

* The user home directory is mounted in the esis container as */data*. This
  must be taken into account when passing a directory to the *index* subcommand
  using a path in the container, not in the host machine.
