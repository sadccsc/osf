
fdate=2024-Jul
seasons=("JAS" "ASO" "SON" "OND")

for lt in 0 1 2 3; do

files=`ls maps/forecast/*/seas/sadc/PRCP/*/*_${fdate}_${lt}.jpg`

seas="${seasons[$lt]}"
echo $seas

for file in $files;do
	outfile=${file/_${fdate}_${lt}/_${fdate}_${seas}}
	mv $file $outfile

done

done
