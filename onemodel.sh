#!/bin/bash
#
# script to call python script to download data and process seasonal forecast for a single model, single variable 
#
# P.Wolski
# March 2024
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
   echo singlefcst.sh lstfile.lst [startdate] [enddate] 
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
    if [ $currentday -le 5 ]; then
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

    for item in ${parameters[@]}; do
        item=(${item//,/ })
        model=${item[0]}
        predictorvar=${item[1]}
        predictordomain=${item[2]}
        predictandinstitution=${item[3]}
        predictandvar=${item[4]}
        predictanddomain=${item[5]}
        mos=${item[6]}
        basetime=${item[7]}
        regime=${item[8]}
        mask=${item[9]}
        overwrite=${item[10]}

        datadir=$rootdir/data
        mapdir=$rootdir/maps
        args="$datadir $mapdir $model $predictorvar $predictordomain $predictandinstitution $predictandvar $predictanddomain $mos $cdate $basetime $regime $mask $overwrite"
        echo
        echo "*********************************"
        echo calling pycpt_singlemodel.py with $args

        if [ $predictandvar == "onsetD" ]; then

            python $scriptdir/onemodel.py $args
        else
            python $scriptdir/onemodel.py $args
        fi
    done
    cdate=$(date +"%Y%m%d" -d "$cdate + 1 month")
    #exit
done

