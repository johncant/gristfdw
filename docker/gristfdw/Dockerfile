ARG POSTGRES_VERSION
ARG MULTICORN_VERSION

# This base image is the image we use to test gristfdw
# gristfdw is not yet installed here.
FROM gristfdw-base:bullseye-postgres$POSTGRES_VERSION-multicorn$MULTICORN_VERSION

ADD . /opt/gristfdw
WORKDIR /opt/gristfdw

# Now install gristfdw
RUN python setup.py install
