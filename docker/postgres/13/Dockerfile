# TODO - It would be helpful to parametrize the postgres and multicorn versions.
# Unfortunately not yet sure how to do this with tox-docker, so this can wait.

FROM postgres:13-bullseye

RUN DEBIAN_FRONTEND=noninteractive apt-get -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install wget build-essential python3-dev postgresql-server-dev-13 python3-pip git

RUN mkdir -p /opt/multicorn
WORKDIR /opt/multicorn

RUN wget https://github.com/pgsql-io/multicorn2/archive/refs/tags/v2.4.tar.gz
#https://github.com/pgsql-io/multicorn2/

RUN update-alternatives --install /usr/bin/python python `which python3` 1

RUN python -V

RUN tar -xvf v2.4.tar.gz
RUN cd multicorn2-2.4 && make

# pip3.9 did not exist and multicorm make install calls this
RUN ln -s `which pip` /usr/bin/pip3.9

RUN cd multicorn2-2.4 && make install

RUN pip install "git+https://github.com/johncant/py_grist_api@jc_add_list_tables_columns#egg=grist_api"
