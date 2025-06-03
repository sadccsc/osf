#!/bin/bash

wbsgas=192.168.203.4

#if script receives two arguments - set end date
if [ $# == 2 ]; then
    enddate=$2
else
    enddate=$(date +"%Y%m%d")
    currentday=$(date +"%d")
    if [ $currentday -le 5 ]; then
        enddate=$(date +"%Y%m%d" -d "$startdate - 1 months")
    fi
fi

#if one or two arguments - set start date
if [ $# -ge 1 ]; then
    startdate=$1
else
    startdate=$(date +"%Y%m%d" -d "$enddate - 0 months")
fi


echo startdate: $startdate
echo enddate: $enddate


#exit

cdate=$startdate

#iterating through dates
while [ "$cdate" -le $enddate ]; do
    datestr=$(date +"%Y%m" -d $cdate)
    echo $datestr
    echo
    echo ---------------------------------------------------------------------------------------------
    echo syncing seasonal

    for var in PRCP TG CDD Rx5day onsetD; do
        for model in SEAS51 CFSv2 GEOSS2S CCSM4; do 
            echo $var $model
            echo rsync -avog  maps/forecast/${model}/seas/sadc/${var}/${datestr}/ ftpdatapush@${wbsgas}:/var/www/html/media/data/rccsadc/csc/osf-seasonal
            rsync -avog  maps/forecast/${model}/seas/sadc/${var}/${datestr}/* ftpdatapush@${wbsgas}:/var/www/html/media/data/rccsadc/csc/osf-seasonal
        done
        #multi-model ensemble
        rsync -avog  maps/forecast/MME01/seas/sadc/${var}/${datestr}/* ftpdatapush@${wbsgas}:/var/www/html/media/data/rccsadc/csc/osf-seasonal-mme
    done


    echo
    echo ---------------------------------------------------------------------------------------------
    echo syncing monthly
    for var in PRCP TG; do
        for model in SEAS51 CFSv2 GEOSS2S CCSM4; do 
            echo $var $model
            rsync -avog  maps/forecast/${model}/mon/sadc/${var}/${datestr}/* ftpdatapush@${wbsgas}:/var/www/html/media/data/rccsadc/csc/osf-monthly
        done
        #multi-model ensemble
        rsync -avog  maps/forecast/MME01/mon/sadc/${var}/${datestr}/* ftpdatapush@${wbsgas}:/var/www/html/media/data/rccsadc/csc/osf-monthly-mme
    done

    cdate=$(date +"%Y%m%d" -d "$cdate + 1 month")
    #exit
done

