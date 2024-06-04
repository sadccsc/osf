#!/bin/bash
#
# script to call python script to generate local predictand files from data stored in the monitoring directories 
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
   echo localpredictand.sh lstfile.lst
   exit
else
    lstfile=$1
    if [ ! -f $lstfile ]; then
        echo "ERROR. lst file $lstfile does not exist. Stopping execution..."
        exit
    fi 
fi

echo listfile: $lstfile

#reading members list (i.e. list of models to be processed. These are stored in members.txt file
echo reading $lstfile
parameters=()
while read -r line; do
    if [ ! ${line:0:1} == "#" ];then
        parameters+=($line)
    fi
done < $lstfile
echo read ${#parameters[@]} entries


for item in ${parameters[@]}; do
	item=(${item//,/ })
	dataset=${item[0]}
	datatype=${item[1]}
    domain=${item[2]}
	basetime=${item[3]}
	variable=${item[4]}
	aggrfactor=${item[5]}

	datadir=$rootdir/data
	args="$datadir $dataset $datatype $domain $basetime $variable $aggrfactor"
	echo
	echo "*********************************"
	echo calling localpredictand.py with $args

	python $scriptdir/localpredictand.py $args
done

