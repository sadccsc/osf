#! /bin/bash


if [ $# == 0 ]; then
    echo use: ./check.sh date
    echo date format: YYYYMM
    exit
fi

date=$1

ls -lsa data/forecast/*/seas/sadc/*/$date-*/*/output/*forecasts.nc
