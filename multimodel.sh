#!/bin/bash
#
# script to call python script to process seasonal forecast for a multimodel ensemble single variable 
#
# P.Wolski
# May 2024
#
echo "***********************************************************************************************************************"

#finding path to this script
ABSPATH=$(readlink -f $0)
#this is when other scripts are in the same directory as this file, otherwise scriptdir will need to be defined here explicitly
scriptdir=$(dirname $ABSPATH)

source $scriptdir/pycptEnv

#if script receives no arguments - stop execution
if [ $# == 0 ]; then
   echo ERROR. This script requires at least one argument - the name of the lst file. None provided. Stopping execution...
   echo Expected usage:
   echo pycpt_multimodel.sh lstfile.lst [startdate] [enddate] 
   exit
else
    lstfile=$1
    if [ ! -f $lstfile ]; then
        echo "ERROR. lst file $lstfile does not exist. Stopping execution..."
        exit
    fi 
fi

#if script receives three arguments - set end date
if [ $# == 3 ]; then
    enddate=$3
else
    enddate=$(date +"%Y%m%d")
    currentday=$(date +"%d")
    if [ $currentday -le 10 ]; then
        enddate=$(date +"%Y%m%d" -d "$startdate - 1 months")
    fi
fi


#if two or more arguments - set start date
if [ $# -ge 2 ]; then
    startdate=$2
else
    startdate=$(date +"%Y%m%d" -d "$enddate - 0 months")
fi

echo listfile: $lstfile
echo startdate: $startdate
echo enddate: $enddate


#reading members list (i.e. list of models to be processed. These are stored in members.txt file
echo reading $lstfile
parameters=()
while read -r line; do
    if [ ! ${line:0:1} == "#" ];then
        parameters+=($line)
    fi
done < $lstfile
echo read ${#parameters[@]} entries


cdate=$startdate

#iterating through dates
while [ "$cdate" -le $enddate ]; do
   
    echo
    echo
    echo "************************************************************"
    echo current date: $cdate

    datadir=$rootdir/data
    mapdir=$rootdir/maps

    for item in ${parameters[@]}; do
	item=(${item//,/ })
        n=${#item[@]}
	echo found $n entries
        args="$datadir $mapdir $cdate"
	for entry in ${item[@]}; do
            args="$args $entry"
	done
        echo
        echo "*********************************"
        echo calling pycpt_multimodel.py with $args


        python $scriptdir/multimodel.py $args
    done
    cdate=$(date +"%Y%m%d" -d "$cdate + 1 month")
    #exit
done

