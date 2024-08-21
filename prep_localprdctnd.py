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
    spatialaggrfactor=int(sys.argv[7])
    timeaggr=sys.argv[8]
else:
    datadir="./data"
    institution="ERA5"
    datatype="reanalysis"
    domain="sadc"
    basetime="mon"
    variable="TX"
    spatialaggrfactor=5

overwrite=False

#this is missing value present in the input file
missingvalue=-999

firstyear=1992
lastyear=2024

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

dates=pd.date_range(pd.to_datetime(data.time[0].data),pd.to_datetime(data.time[-1].data), freq="ME")

print("Found data for {} months covering period of {} to {}".format(len(data.time.data), pd.to_datetime(data.time[0].data), pd.to_datetime(data.time[-1].data))) 
if len(data.time.data)<len(dates):
    print("ERROR. Data missing. There should be {} in data period of {} to {} got {} months".format(len(dates), pd.to_datetime(data.time[0].data), pd.to_datetime(data.time[-1].data), len(data.time.data)))
    sys.exit()

#check
if spatialaggrfactor>1:
    data=data.coarsen(lat=spatialaggrfactor).mean().coarsen(lon=spatialaggrfactor).mean()

if "spatial_ref" in data.variables:
    data=data.drop_vars({"spatial_ref"})

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#there should be no need to edit anything below
if basetime=="seas":
    #fcstmonth 0 is january, and should give data for NDJ
    seasons=["NDJ","DJF","JFM","FMA","MAM","AMJ","MJJ","JJA","JAS","ASO","SON","OND"]

    #lastfcstmonths=range(1,13)
    if timeaggr=="sum":
        data=data.rolling(time=3).sum()
    elif timeaggr=="max":
        data=data.rolling(time=3).max()
    elif timeaggr=="min":
        data=data.rolling(time=3).min()
    elif timeaggr=="mean":
        data=data.rolling(time=3).mean()
    else:
        print("ERROR. Not able to process temporal aggregation {}".format(timeaggr))
        sys.exit()
    

elif basetime=="mon":
    #fcstmonth 0 is january, and should give data for January
    seasons=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

else:
    print("ERROR. Not able to process basetime {}".format(basetime))
    sys.exit()


for fcstmonth in range(12):
    #Rolling operation gives time value of the last time step in the rolling window
    #months are indexed from 0, but 0 corresponds to calendar month 1
    data1=data.sel(time=data.time.dt.month==(fcstmonth+1)).sel(time=slice(str(firstyear),str(lastyear)))
    seasonname=seasons[fcstmonth]

    if basetime=="seas":
        # deriving season name
        #pycpt data have to have date of the middle month of the season, thus date is now offset by one month
        data1["time"]=(pd.to_datetime(data1.time)-pd.DateOffset(months=1)+pd.DateOffset(days=15)).normalize()
    else:
        data1["time"]=(pd.to_datetime(data1.time)+pd.DateOffset(days=15)).normalize()

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




