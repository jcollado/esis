========
Usage
========

As a python library
-------------------

To use *esis* in a project just import the *Client* object from the *esis*
package and call any of the following methods: *index*, *count*, *search* and
*query*.

.. code-block:: python

    from esis import Client

    client = Client()
    client.index(directory)
    client.count()
    client.search(query)
    client.clean()

.. note::

    The client method names match the command line tool subcommand names as it
    can be seen in next section.

As a command line tool
----------------------

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


In docker containers
--------------------

Using docker-compose
~~~~~~~~~~~~~~~~~~~~

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

Using docker
~~~~~~~~~~~~

If you want to use *docker* instead of *docker-compose*, you just need to follow the steps below.

* Download the images

.. code-block:: bash

    docker pull elasticsearch
    docker pull jcollado/esis

* Start Elasticsearch

.. code-block:: bash

    docker run --name elasticsearch elasticsearch

where the *--name* option is used to have a known container name that can be
used later to link the Elasticsearch container to the esis one.

The entry point for the esis image assumes that the hostname for Elasticsearch
is elasticsearch in the container. Take this into account when using the
*--link* option as in the examples below.

* Run esis

    * Index data under directory

    .. code-block:: bash

        docker run --link elasticsearch:elasticsearch -v <directory>:/data --rm -t -i jcollado/esis index /data

    where *<directory>* is a location in the host filesystem and */data* is an
    arbitrary directory used to index data in the container.

    * Count indexed documents

    .. code-block:: bash

        docker run --link elasticsearch:elasticsearch --rm -t -i jcollado/esis count

    * Run search query

    .. code-block:: bash

        docker run --link elasticsearch:elasticsearch --rm -t -i jcollado/esis search <string>

    where *<string>* is the string to be used in the query against Elasticsearch.

    * Remove indexed documents

    .. code-block:: bash

        docker run --link elasticsearch:elasticsearch --rm -t -i jcollado/esis clean
