FROM python:2.7-onbuild
MAINTAINER Javier Collado <jcollado@nowsecure.com>
RUN python setup.py develop
ENTRYPOINT ["esis", "--host", "elasticsearch"]
