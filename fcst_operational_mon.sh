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
$ABSDIR/onemodel.sh onemodel_operational_mon.lst
$ABSDIR/multimodel.sh multimodel_operational_mon.lst

