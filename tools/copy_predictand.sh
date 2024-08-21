
predictor=SST-global
for tgtdate in 202407-JAS 202407-ASO 202407-SON 202407-OND; do
	infile=data/forecast/SEAS51/seas/sadc/PRCP/$tgtdate/$predictor/data/UCSB.PRCP.nc

	for model in CanSIPSIC3 SPEAR CCSM4 GEOSS2S; do
		#for predictor in SST-nino34 SST-global PRCP-sadc GPH-saf; do 
			datadir=data/forecast/$model/seas/sadc/PRCP/$tgtdate/$predictor/data/
			if [ ! -e $datadir ]; then
				mkdir -p $datadir
			fi
			outfile=$datadir/UCSB.PRCP.nc
			if [ ! -e $outfile ]; then
			    echo copying $outfile
			    cp $infile $outfile
			fi
#        done
	done

done
