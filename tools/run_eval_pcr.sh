#./eval.sh single_nino.lst 20230601 20230930 SON
#./eval.sh single_global.lst 20230601 20230930 SON
#./eval.sh single_rain.lst 20230601 20230930 SON
#./eval.sh single_gph.lst 20230601 20230930 SON

startdate=20230901
enddate=20231230
season=DJF
screen -S gphpcr$season -d -m bash -c "./eval.sh single_gph_pcr.lst $startdate $enddate $season"

startdate=20231201
enddate=20240330
season=MAM

screen -S gphpcr$season -d -m bash -c "./eval.sh single_gph_pcr.lst $startdate $enddate $season"

startdate=20230601
enddate=20230930
season=SON
screen -S gphpcr$season -d -m bash -c "./eval.sh single_gph_pcr.lst $startdate $enddate $season"

#screen -S nino$season -d -m bash -c "./eval.sh single_nino.lst $startdate $enddate $season"
#screen -S global$season -d -m bash -c "./eval.sh single_global.lst $startdate $enddate $season"
#screen -S rain$season -d -m bash -c "./eval.sh single_rain.lst $startdate $enddate $season"
#screen -S gph$season -d -m bash -c "./eval.sh single_gph.lst $startdate $enddate $season"

startdate=20230701
enddate=20230730
season=SON
#./eval.sh single_nino.lst $startdate $enddate $season
