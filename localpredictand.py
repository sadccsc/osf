#!/usr/bin/env python
# coding: utf-8

# In[7]:


#
# importing ERA5 monthly temperature data and converting them to seasonal total for use with PyCPT
#
# by P.Wolski
#
# May 2024
#

import cptio as cio
import xarray as xr
import os,sys
import pandas as pd


# In[17]:


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#User-defined arguments

#this is variable to be processed. possible values: TMAX,TMIN,TMEAN
parseargs=True

if parseargs==True:
    datadir=sys.argv[1]
    institution=sys.argv[2]
    datatype=sys.argv[3]
    domain=sys.argv[4]
    basetime=sys.argv[5]
    variable=sys.argv[6]
    aggrfactor=int(sys.argv[7])
else:
    datadir="./data"
    institution="ERA5"
    datatype="reanalysis"
    domain="sadc"
    basetime="mon"
    variable="TX"
    aggrfactor=5

overwrite=False

#this is missing value present in the input file
missingvalue=-999


if basetime not in ["mon","seas"]:
    print("ERROR. Basetime can only be mon or seas. requested {}".format(basetime))
    sys.exit()
    
#input and output directories
inputdir="{}/{}/{}/mon/{}/{}".format(datadir,datatype,institution,domain,variable)
if not os.path.exists(inputdir):
    print("ERROR. Input directory does not exist. {}".format(inputdir))
    sys.exit()

outputdir="{}/local_predictand/{}/{}/{}/{}".format(datadir,institution,basetime,domain,variable)
if not os.path.exists(outputdir):
    print("output directory does not exist. creating...")
    os.makedirs(outputdir)
    print("created {}".format(outputdir))
    
#reading input data
#input data are to be monthly and for the target domain and resolution
#

data=xr.open_mfdataset("{}/{}_mon_{}_{}_*.nc".format(inputdir,variable,institution,domain))

if aggrfactor>1:
    data=data.coarsen(lat=2).mean().coarsen(lon=2).mean()

if "spatial_ref" in data.variables:
    data=data.drop_vars({"spatial_ref"})

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#there should be no need to edit anything below
if basetime=="seas":
    seasons=["JFM","FMA","MAM","AMJ","MJJ","JJA","JAS","ASO","SON","OND","NDJ","DJF"]
    lastfcstmonths=range(1,13)
    
elif basetime=="mon":
    seasons=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    lastfcstmonths=[(((x-1)+2)%12)+1 for x in range(1,13)]
    
for fcstmonth in range(1,13):

    #this is last month of the three month forecast period
    
    # deriving season name
    seasonname=seasons[fcstmonth-1]

    #calculating rolling 3-month mean
    data1=data.rolling(time=3).mean()
    #selecting only target season. 
    #Rolling operation gives time value of the last time step in the rolling window
    #thus selection is based on lastfcstmonth
    data1=data1.sel(time=data1.time.dt.month==lastfcstmonths[fcstmonth-1])
    #pycpt data have to have date of the first month of the season, thus date is now offset by two months
    data1["time"]=(pd.to_datetime(data1.time)-pd.DateOffset(months=2)+pd.DateOffset(days=15)).normalize()
    #renaming variables to the ones used by pycpt
    data1=data1.rename({"lon":"X", "lat":"Y", "time":"T"})
    #adding attributes
    data1[variable].attrs={"missing":missingvalue, "units":"degC"}

    #defining outputfile
    outputfile="{}/{}.{}_{}.tsv".format(outputdir,variable,institution,seasonname)
        
    if os.path.exists(outputfile):
        da = cio.open_cptdataset(outputfile)
        lastfiledate=da["T"][-1]
        lastdatadate=data1["T"][-1]
        da.close()
        
        if lastdatadate>lastfiledate:
            print("data will be stored in {}".format(outputfile))
            writefile=True
        else:
            print("outputfile exists, and there is no new data to add {}".format(outputfile))
            writefile=False
    else:
        writefile=True
        
    if writefile:
        #writing outputfile
        cio.to_cptv10(data1[variable], outputfile)
        print("written",outputfile)
    


# In[ ]:




