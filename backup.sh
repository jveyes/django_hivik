#!/bin/bash

# Set the database connection details
PGHOST="ec2-52-6-117-96.compute-1.amazonaws.com"
PGDATABASE="dao4gcco5kbsfa" 
PGUSER="ztklwuglyluaih"
PGPASSWORD="9e5695fa52bc9d87b4c9c26cea09aec077e4800771005594b8c6e216f90ba688"
PGPORT="5432"

# Set the backup file name and location
BACKUP_FILE="/c/Users/medin/Desktop/django_hivik/(date +%Y%m%d).sql"

# Create the backup
pg_dump -h $PGHOST -d $PGDATABASE -U $PGUSER -p $PGPORT -f $BACKUP_FILE

# Verify the backup
if [ $? -eq 0 ]; then
    echo "Backup successful: $BACKUP_FILE"
else
    echo "Backup failed."
fi
