from docker.io/bitnami/postgresql-repmgr:11
USER root
RUN apt-get update && apt-get install zip curl
ADD dbout.sh /docker-entrypoint-initdb.d/0.sh
USER 1001
