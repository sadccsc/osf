srcdate=202312-MAM
srcmodel=CanSIPSIC3
srcmodel=CCSM4
srcpred=SST-nino34

#for tgtmon in 01 02 03; do
#tgtdate=2024$tgtmon-MAM

for tgtmon in 12; do
tgtdate=2023$tgtmon-DJF
infile=UCSB.PRCP-DJF.nc

	#for model in CFSv2 ; do
	for model in CanSIPSIC3 SEAS51 METEOFRANCE8 GCFS2p1 SPSv3p5 SPEAR CCSM4 GEOSS2S CFSv2 ; do
		#for predictor in SST-nino34 SST-global PRCP-sadc GPH-saf; do 
		for predictor in GPH-saf; do 
			outdir=data/forecast/$model/seas/sadc/PRCP/$tgtdate/$predictor/data/
			if [ ! -e $outdir ]; then
				mkdir -p $outdir
			fi

			#outfile=$outdir/UCSB.PRCP.nc
			#infile=./data/forecast/$srcmodel/seas/sadc/PRCP/$srcdate/$srcpred/data/UCSB.PRCP.nc
			outfile=$outdir/UCSB.PRCP.nc
#            echo $outfile

			if [ ! -e $outfile ]; then
			    echo copying $outfile
			    cp $infile $outfile
			fi

		done
	done

done
