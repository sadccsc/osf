#! /bin/bash


if [ $# == 0 ]; then
    echo use: ./check.sh date
    echo date format: YYYYMM
    exit
fi

date=$1

for model in SEAS51 CCSM4 CFSv2 GEOSS2S; do
    echo 
    for var in PRCP Rx5day CDD TG; do
        n=`ls data/forecast/$model/seas/sadc/$var/$date-*/*/output/*forecasts.nc |wc -l`

        echo $model $var $n
    done
done
