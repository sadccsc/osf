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

#processing single model and multi-model forecasts
$ABSDIR/onemodel.sh onemodel_operational_seas.lst
$ABSDIR/multimodel.sh multimodel_operational_seas.lst

