for srcdate in 202407-JAS 202407-ASO 202407-SON 202407-OND; do
    tgtdate=$srcdate
	for model in CFSv2 ; do
		for predictor in SST-global; do
			outdir=data/forecast/$model/seas/sadc/TG/$tgtdate/$predictor/data/
			if [ ! -e $outdir ]; then
				mkdir -p $outdir
			fi
			infile=./data/forecast/$model/seas/sadc/PRCP/$srcdate/$predictor/data/${model}*
			outfile=$outdir/
            echo $outfile
#			if [ ! -e $outfile ]; then

				echo copying $outfile
				cp $infile $outfile
#			fi

		done
	done
done
