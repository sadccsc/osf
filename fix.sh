
files=`ls -d data/forecast/SEAS51/mon/sadc/PRCP/*/SST-nino34/nino34/*`
for file in $files;do
outfile=${file/nino34/SST-nino34}
echo mv $file 
#$outfile

done

