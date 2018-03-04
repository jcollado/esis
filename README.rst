===============================
Elasticsearch Index & Search
===============================

.. image:: https://img.shields.io/pypi/l/esis.svg
    :target: https://pypi.python.org/pypi/esis/
    :alt: License

.. image:: https://img.shields.io/pypi/v/esis.svg
    :target: https://pypi.python.org/pypi/esis

.. image:: https://readthedocs.org/projects/esis/badge/?version=latest
    :target: http://esis.readthedocs.org/en/latest/
    :alt: Documentation

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

.. image:: http://unmaintained.tech/badge.svg
    :alt: No Maintenance Intended
    :target: http://unmaintained.tech/


Elasticsearch Index & Search, *esis* for short, is a tool to easily search for
information in the files available under a given directory in the filesystem.


Features
--------

* Index content for every SQLite database row in Elasticsearch
* Search indexed content

Why?
----

*esis* is based on the code used in a `mobile forensics product
<https://www.nowsecure.com/forensics/>`_. An important use case of such a
product is to extract data from a mobile device and provide a way for
investigators to search relevant information in that data. Since most of that
data is stored in SQLite databases, it makes sense to figure out a way to
perform that operation in an efficient way and Elasticsearch has been a good
solution to that problem so far.

The tool was initially released as a companion to the presentation `how to
search extracted data
<http://www.slideshare.net/javier.collado/how-to-search-extracted-data>`_ that
was given at `DFRWS EU 2015 <http://dfrws.org/2015eu/program.shtml>`_
