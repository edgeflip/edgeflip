#!/bin/bash
SCRIPT=`readlink -f $0`
SCRIPTPATH=`dirname $SCRIPT`

sqlfile=`readlink -f $SCRIPTPATH/../sql/initial.sql`
echo "Executing $sqlfile"
mysql -u root -p < "$sqlfile"
