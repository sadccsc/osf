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

date=202408
for var in PRCP TG CDD Rx5day; do
    for model in SEAS51 CFSv2 GEOSS2S CCSM4; do 
        echo $var $model
        rsync -avog  maps/forecast/${model}/seas/sadc/${var}/${date}/* ftpdatapush@${wbsgas}:/var/www/html/media/data/rccsadc/csc/osf-seasonal
    done
    #multi-model ensemble
    rsync -avog  maps/forecast/MME01/seas/sadc/${var}/${date}/* ftpdatapush@${wbsgas}:/var/www/html/media/data/rccsadc/csc/osf-seasonal-mme
done


echo
echo ---------------------------------------------------------------------------------------------
echo syncing monthly
for var in PRCP TG; do
    for model in SEAS51 CFSv2 GEOSS2S CCSM4; do 
        echo $var $model
        rsync -avog  maps/forecast/${model}/mon/sadc/${var}/${date}/* ftpdatapush@${wbsgas}:/var/www/html/media/data/rccsadc/csc/osf-monthly
    done
    #multi-model ensemble
    rsync -avog  maps/forecast/MME01/mon/sadc/${var}/${date}/* ftpdatapush@${wbsgas}:/var/www/html/media/data/rccsadc/csc/osf-monthly-mme
done


