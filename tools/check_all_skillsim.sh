#for fcst in 202401-MAM 202402-MAM 202403-MAM 202312-MAM; do
#for fcst in 202306-SON 202307-SON 202308-SON 202309-SON; do
#for fcst in 202309-DJF 202310-DJF 202311-DJF 202312-DJF; do
    echo "********************************************************************************"
    echo $fcst
	for model in SEAS51 METEOFRANCE8 GCFS2p1 SPSv3p5 SPEAR CCSM4 GEOSS2S CFSv2 CanSIPSIC3; do
		for pred in SST-global SST-nino34 GPH-saf PRCP-sadc; do
			searchpattern=/storageserver/RCC/data/forecast/$model/seas/sadc/PRCP/$fcst/$pred/output/*cca.nc
			#echo $searchpattern
			n=`ls /storageserver/RCC/data/forecast/$model/seas/sadc/PRCP/$fcst/$pred/output/*cca.nc 2> /dev/null |wc -l`
			if [ $n -eq 0 ]; then
			echo missing output: $fcst $pred $model
            echo /storageserver/RCC/data/forecast/$model/seas/sadc/PRCP/$fcst/$pred/data/
            input=`ls /storageserver/RCC/data/forecast/$model/seas/sadc/PRCP/$fcst/$pred/data/`
            echo $input
			fi
		done
	done
done
