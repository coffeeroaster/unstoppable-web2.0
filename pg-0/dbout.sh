#!/bin/bash
set -x

if [[ ! -f /tmp/dbout.zip ]] 
then
curl "$BACKUP_SKYNET_URL" > /tmp/dbout.zip
fi

# unzip file from skynet
unzip -P "$BACKUP_PASS" -p /tmp/dbout.zip > /tmp/dbout.sql


# import into postgres
PGPASSWORD="$POSTGRESQL_PASSWORD" psql -U "$POSTGRESQL_USERNAME"  "$POSTGRESQL_DATABASE" < /tmp/dbout.sql 
rm /tmp/dbout.sql
