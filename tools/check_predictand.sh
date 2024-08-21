
tgtmon=04
#for fcst in 202401-MAM 202402-MAM 202403-MAM 202312-MAM; do
#tgtmon=01
#for fcst in 202309-DJF 202310-DJF 202311-DJF 202312-DJF; do
#tgtmon=10
#for fcst in 202306-SON 202307-SON 202308-SON 202309-SON; do
#tgtmon=10
#for fcst in 202407-SON; do
#tgtmon=08
#for fcst in 202407-JAS; do
tgtmon=09
for fcst in 202407-ASO; do
    echo "********************************************************************************"
    echo $fcst
	for model in SEAS51 METEOFRANCE8 GCFS2p1 SPSv3p5 SPEAR CCSM4 GEOSS2S CFSv2 CanSIPSIC3; do
		for pred in SST-global SST-nino34 GPH-saf PRCP-sadc; do
		
		predictorfile=/storageserver/RCC/data/forecast/$model/seas/sadc/PRCP/$fcst/$pred/data/UCSB.PRCP.nc
		predictorfile=/storageserver/RCC/data/forecast/$model/seas/sadc/PRCP/$fcst/$pred/output/${model}.SST_realtime_pcr_forecasts.nc
        if [ ! -f $predictorfile ]; then
            #echo $predictorfile does not exist.
            cont=true
        else
                echo $fcst $pred $model
            res=(`cdo -showdate $predictorfile 2> /dev/null`)
            res=${res[0]}
            echo $res
            res=(${res//-/ })
            if [ ${res[1]} != $tgtmon ]; then
                echo ERROR ${res[1]} $fcst $pred $model
            fi
        fi
		done
	done
done
