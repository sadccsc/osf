#! /bin/bash

#
# master script to process forecasts with pycpt
#
# P.Wolski
# July 2024
#

#some housekeeping
ABSPATH=$(readlink -f $0)
ABSDIR=$(dirname $ABSPATH)

#downloading individual datasets
$ABSDIR/onemodel.sh onemodel.lst

