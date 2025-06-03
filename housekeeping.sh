#! /bin/bash

today=$(date +"%Y%m%d")

mkdir -p logs/$today

echo moving log files to logs/$today

for file in `ls logs/*.log`; do
    mv $file logs/$today/
done
echo done


