srcdate=202407-JAS
tgtdate=$srcdate
srcmodel=SEAS51
srcpred=SST-global

#for srcdate in 202407-JAS 202407-ASO 202407-SON 202407-OND; do
for srcdate in 202407-Jul 202407-Aug 202407-Sep 202407-Oct 202407-Nov; do
    tgtdate=$srcdate
	#for model in CanSIPSIC3 SEAS51 METEOFRANCE8 GCFS2p1 SPSv3p5 SPEAR CCSM4 GEOSS2S CFSv2 ; do
	for model in CFSv2 ; do
		for predictor in SST-global; do 
			outdir=data/forecast/$model/mon/sadc/PRCP/$tgtdate/$predictor/data/
			if [ ! -e $outdir ]; then
				mkdir -p $outdir
			fi
			infile=./data/forecast/$srcmodel/mon/sadc/PRCP/$srcdate/$srcpred/data/UCSB.PRCP.nc
			outfile=$outdir/UCSB.PRCP.nc
            echo $outfile
			if [ ! -e $outfile ]; then
				echo copying $outfile
				cp $infile $outfile
			fi

		done
	done
done
