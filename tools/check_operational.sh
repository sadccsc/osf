fcst=202408

for basetime in mon seas; do
    echo "********************************************************************************"
    if [ $basetime == "mon" ]; then
        vars=("PRCP" "TG")
    else
        vars=("PRCP" "TG" "CDD" "Rx5day")
    fi
    for var in ${vars[@]} ; do
    echo "***********************************"
        if [[ $var == "PRCP" || $var == "CDD" || $var == "Rx5day" ]]; then
            pred=SST-global
        else
            pred=T2M-sadc
        fi
        echo $fcst $basetime $var
        for model in SEAS51 CFSv2 GEOSS2S CCSM4 ;do
            #/storageserver/RCC/data/forecast/CCSM4/seas/sadc/PRCP/202407-JAS/SST-global/output/
            searchpattern=/storageserver/RCC/data/forecast/$model/$basetime/sadc/$var/${fcst}*/$pred/output/*pcr.nc
            #echo $searchpattern
            #n=`ls /storageserver/RCC/data/forecast/$model/$basetime/sadc/$var/${fcst}*/$pred/output/*pcr.nc 2> /dev/null |wc -l`
            n=`ls $searchpattern 2> /dev/null |wc -l`
            echo $model $n
        done
    done
done
