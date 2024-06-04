#!/bin/bash

wbsgas=192.168.203.4

if [ $# -ne 0 ] ; then
  today=$1
else
  today=$(date +"%Y%m%d" -u)
fi
echo $today

echo
echo ---------------------------------------------------------------------------------------------
echo syncing seasonal
rsync -avog  maps/forecast/SEAS51/seas/sadc/PRCP/* ftpdatapush@${wbsgas}:/var/www/html/media/data/rccsadc/csc/osf-seasonal

