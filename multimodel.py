#!/usr/bin/env python
# coding: utf-8

# In[1]:


#!/usr/bin/env python
# coding: utf-8

# ============================================================================================
# importing libraries

# original libraries from IRI version
import pycpt
import packaging
min_version = '2.5.0'
assert packaging.version.parse(pycpt.__version__) >= packaging.version.parse(min_version), f'This notebook requires version {min_version} or higher of the pycpt library, but you have version {pycpt.__version__}. Please close the notebook, update your environment, and load the notebook again. See https://iri-pycpt.github.io/installation/'

import cptdl as dl 
from cptextras import get_colors_bars
import datetime as dt
import numpy as np
from pathlib import Path
import xarray as xr

import pandas as pd
import numpy as np
import datetime
#from mpl_toolkits.basemap import Basemap #only needed by the original pycpt plotting functions
import matplotlib.colors as colors
import matplotlib.pyplot as plt

# libraries added to support functionality at CSC
import os,sys
import functions_plot as fun
from functions_pycpt import *
import textwrap

# In[23]:


# ============================================================================================
# parsing parameters defining the forecast
#

# parsing forecast parameters from command line arguments - target season, domain, model etc..
#
#in operational setting - these are the only values that will have to change from month to month
#
datadir=sys.argv[1]
mapdir=sys.argv[2]
init_date=sys.argv[3]
mmecode=sys.argv[4]
predictand_institution=sys.argv[5]
predictand_var=sys.argv[6]
predictand_domain=sys.argv[7]
basetime=sys.argv[8]
skill_mask_code=sys.argv[9]
overwrite=bool(int(sys.argv[10]))
nargs=len(sys.argv)
print(nargs)
nargserror=(nargs-10-1)%4
if nargserror>0:
    print("there have to be three arguments passed per member of the ensmble. There is {} too many".format(nargserror))
    sys.exit()
currentarg=10
ensemblemembers=[]
while nargs-1>currentarg:
    model=sys.argv[currentarg+1]
    predictor_var=sys.argv[currentarg+2]
    predictor_domain=sys.argv[currentarg+3]
    MOS=sys.argv[currentarg+4]
    ensemblemembers.append([model,predictor_var,predictor_domain,MOS])
    currentarg=currentarg+4

# In[29]:


# ============================================================================================
# forecast parameters defined "in script"
#
# first and last year of the hindcast. This is set here to be the same for each forecast model, but potentially can be diversified between models
first_hindcast_year,last_hindcast_year=1993,2015

#is where all data - inputs and outputs are going to be stored. Sub-directory structure will be created automatically in this root directory to capture target domain, predictand, models, initializtion date, target season etc...
# this one has to be changed/adjusted if scripts are moved or a different directory structure is used
fcstrootdir="{}/forecast/{}".format(datadir,mmecode)
localpredictandrootdir="{}/local_predictand".format(datadir)
maprootdir="{}/forecast/{}".format(mapdir,mmecode)

predictor_domain_file="./dictionaries/predictor_domains.json"
predictand_domain_file="./dictionaries/predictand_domains.json"
obs_ncvars_file="./dictionaries/obs_ncvars.json"
labels_file="./dictionaries/labels.json"
local_predictands_file="./dictionaries/local_predictands.json"


#this defines level of messages that this script is going to return to log
verbose=True

#defining whether or not calibration diagnostics are plotted
# note that as per March 2024, eofs plotting crashes if MOS is PCR! It is a bug, and IRI are aware... 
do_plot_eof_modes=False
do_plot_cca_modes=False

#internal pycpt parameter that describes whether or not data are to be re-downloaded 
force_download = False

#whether forecast calibration is done intgeractively
interactive = False

#these skill metrics will be plotted:
#names correspond to skill metrics available in the output of pycpt.evaluate_models()
skill_metrics_to_plot = [
        "rpss",
        "genroc",
        "spearman",
        "pearson",
        "2afcmme"
]

# reading dictionaries before proceeding...

local_predictands=parse_json(local_predictands_file)
obs_ncvars=parse_json(obs_ncvars_file)
labels=parse_json(labels_file)
source=read_dict(labels,"MME","labels")
full_source_name="{} model".format(source)


predictand_name="{}.{}".format(predictand_institution,predictand_var)
temp=read_dict(obs_ncvars,predictand_name,"obs_ncvars")

predictand_category=temp[1]

print("category",predictand_category)


#these forecast metrics will be plotted
#these names are "bespoke", implemented in this script only, they are not "native" to pycpt
#defined as a function of predictand 
if predictand_category=="rainfall":
    fcst_outputs_to_plot=["det",
        "det-absanom",
        "prob-tercile"]
else:
    fcst_outputs_to_plot=["det",
        "det-absanom",
        "prob-tercile"]

#these lead time will be calculated for different basetimes
leadtimes={"seas": [0,1,2,3],
        "mon": [0,1,2,3,4]}

  
    
# ============================================================================================
#
# defining dictionaries and functions
#
# these will be used by different functions to get parameters for the forecast 
# as requested by the arguments passed to this script
#
   

#this sets up whether plotting is done with and/or without mask
skillmasks={"no":[[False,""]],
"yes":[[True,"-m"]],
"both":[[False,""], [True,"-m"]]}



   
# ============================================================================================
# picking up parameters for the requested forecast
#


#domain parameters
predictor_domain_params = get_domain_params(predictor_domain_file,predictor_domain)

#overlay file is used for plotting, and it is read here, because it is domain-specific
predictand_domain_params,overlayfile = get_domain_params(predictand_domain_file,predictand_domain)


predtxt="{}.{}".format(predictand_institution,predictand_var)

#catching possible errors... 
if predtxt not in labels.keys():
    print("ERROR: There is no entry for requested predictand in labels dictionary: {}".format(predtxt))
    sys.exit()
    
predictand_dataset_label=labels[predtxt]

#catching possible errors... 
if predictand_var not in labels.keys():
    print("ERROR: There is no entry for requested predictand variable in labels dictionary: {}".format(predictand_var))
    sys.exit()

fcstvar_label=labels[predictand_var]


    
# ============================================================================================
# setting internal parameters of pycpt
#

#these are user-defined, so they have to be set here explicitly rather than later in the middle of other code
cpt_args = { 
    'transform_predictand': None,  # transformation to apply to the predictand dataset - None, 'Empirical', 'Gamma'
    'tailoring': None,  # tailoring None, 'Anomaly'
    'cca_modes': (1,3), # minimum and maximum of allowed CCA modes 
    'x_eof_modes': (1,8), # minimum and maximum of allowed X Principal Componenets 
    'y_eof_modes': (1,6), # minimum and maximum of allowed Y Principal Components 
    'validation': 'crossvalidation', # the type of validation to use; only 'crossvalidation' is supported for now
    'drymask': False, #whether or not to use a drymask of -999
    'scree': True, # whether or not to save % explained variance for eof modes
    'crossvalidation_window': 5,  # number of samples to leave out in each cross-validation step 
    'synchronous_predictors': True, # whether or not we are using 'synchronous predictors'
}
print("done")

# In[31]:


# ============================================================================================
#
# processing starts here
#

#iterating through lead times
#for lead_time in leadtimes[basetime]:
for lead_time in [3]:
    print()
    print("----------------------------------")
    print("processing lead time: {}".format(lead_time))
    
    #processing forecast date and target information
    #this returns a dictionary
    season_params = get_season_params(lead_time, init_date, basetime)
     # this is target season's code, e.g. JFM
    target_seas=season_params["target_seas"]
    
    if verbose:
        print("season parameters:\n",season_params)

    fcsts=[]
    hcsts=[]
    ensemble=[]
    predictor_names=[]

    for model, predictor_var, predictor_domain, MOS in ensemblemembers:

        # To read predictand data from a local file instead,
        # set local_predictand_file to the full pathname of the file. e.g.
        # local_predictand_file = "/home/aaron/src/pycpt_notebooks/obs_PRCP_Oct-Dec.tsv"
        
        #here, local predictand file is picked up if predictand variable and predictand institution 
        # are in the local predictands dictionary defined above
        
        local_predictand_file = None

        if predictand_name in local_predictands["code"]:
            # internal parameter of pycpt - if set, then local file is used as predictand
            print("using local predictand")
            
        else:
            print("using predictand from IRI: {}".format(predictand_name))
            if predictand_name not in dl.observations.keys():
                print("ERROR. Could not find predictand {}".format(predictand_name))
                sys.exit()
            
        # Use dl.observations.keys() to see all options for predictand 
        # and dl.hindcasts.keys() to see all options for predictors.
        # Make sure your first_year & final_year are compatible with 
        # your selections for your predictors and predictands.

        predictor_name="{}.{}".format(model,predictor_var)

        if verbose:
            print("predictor:", predictor_name)
            print("predictand:", predictand_name)

        #checking if predictors and predictand are defined correctly
        if predictor_name not in dl.hindcasts.keys():
            print("ERROR. Could not find predictor {} in IRI library. Perhaps a typo?".format(predictor_name))
            sys.exit()
            
        #checking if root directory exists
        if not os.path.exists(fcstrootdir):
            print("ERROR. Root directory ({}) does not exist".format(fcstrootdir))
            sys.exit()
            
        #this is definition of source directory

        memberrootdir="{}/forecast/{}".format(datadir,model)
        case_dir = "{}/{}/{}/{}/{}-{}/{}-{}".format(memberrootdir,
                                 basetime,
                                 predictand_domain,
                                 predictand_var,
                                 season_params["fdate"].strftime("%Y%m"),
                                 target_seas,
                                 predictor_var,
                                 predictor_domain)
 
        print("case_dir",case_dir)

        inputdir="{}/output".format(case_dir)
        predictanddir="{}/data".format(case_dir)
        if not os.path.exists(inputdir):
            print("ERROR. directory with single model forecast output does not exist. Expected to find it here, but alas! {}".format(inputdir))
            sys.exit()

        if not os.path.exists(predictanddir):
            print("ERROR. directory with single model forecast input does not exist. Expected to find it here, but alas! {}".format(predictanddir))
            sys.exit()

        # checking overwrite
        inputfcstfile="{}/{}_realtime_{}_forecasts.nc".format(str(inputdir), predictor_name, MOS.lower())
        inputhcstfile="{}/{}_crossvalidated_{}_hindcasts.nc".format(str(inputdir), predictor_name, MOS.lower())
        predictandfile="{}/{}.nc".format(str(predictanddir), predictand_name)

        if not os.path.exists(inputfcstfile):
            print("ERROR. forecast file does not exist, but required. Expected to find it here, but alas! {}".format(inputfcstfile))
            sys.exit()
        if not os.path.exists(inputhcstfile):
            print("ERROR. hindcast file does not exist, but required. Expected to find it here, but alas! {}".format(inputhcstfile))
            sys.exit()
        if not os.path.exists(predictandfile):
            print("ERROR. predictand file does not exist, but required. Expected to find it here, but alas! {}".format(predictandfile))
            sys.exit()

        fcst=xr.open_dataset(inputfcstfile)
        # this compensates for a bug in pyCPT that requires coordinate S to be present in forecast fed to construct_mme()
        if "S" not in fcst.coords:
            fcst=fcst.assign_coords(S=fcst.T)

        hcst=xr.open_dataset(inputhcstfile)
        fcsts.append(fcst)
        hcsts.append(hcst)

        ensemble.append(predictor_name)
        predictor_names.append(predictor_name)


    #must implement finding temporal overlap of all the models contributing to the mme
    seldates=hcsts[0].T
    for hcst in hcsts:
        sel=hcst.T.isin(seldates)
        seldates=hcst.T[sel]

    hcstsovlp=[]
    for hcst in hcsts:
        hcst=hcst.sel(T=seldates)
        hcstsovlp.append(hcst)
     
    #sys.exit()

    fcstdir = "{}/{}/{}/{}/{}-{}/{}".format(fcstrootdir,
                                 basetime,
                                 predictand_domain,
                                 predictand_var,
                                 season_params["fdate"].strftime("%Y%m"),
                                 target_seas,
                                 mmecode)
    fcstdir = Path(fcstdir)
    outputdir="{}/output".format(str(fcstdir))
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
        
    #unfortunately, the file name that comes out of pycpt is not very informative, and we cannot change it, because edits in pycpt code would get lost after version update, so unfortunately, we have to live with this
    fcstfile="{}/output/MME_deterministic_forecast_{}.nc".format(str(fcstdir), season_params["fyear"])
    #now processing the forecast

    dset=xr.open_dataset(predictandfile)
    ncvar=obs_ncvars[predictand_name][0]
    Y=dset[ncvar]
    dset.close()

 
    if overwrite or (not os.path.exists(fcstfile)):
        print("processing forecast to {}".format(fcstfile))
        det_fcst, pr_fcst, pev_fcst, nextgen_skill = pycpt.construct_mme(fcsts, hcstsovlp, Y, ensemble, predictor_names, cpt_args, fcstdir)

        det_fcst=det_fcst.to_dataset(name="deterministic")
        pr_fcst=pr_fcst.to_dataset(name="probabilistic")
        calibrated=True
        print("done")
    else:
        calibrated=False
        print("forecast file {} exists. skipping calibration...".format(fcstfile)) 





    if not calibrated:
        print("Opening forecast files...")
        skillfile="{}/output/MME_skill_scores.nc".format(str(fcstdir))
        dset=xr.open_dataset(skillfile)
        nextgen_skill=dset.copy()
        dset.close()

        detfcstfile="{}/output/MME_deterministic_forecast_{}.nc".format(str(fcstdir), season_params["fyear"])
        dset=xr.open_dataset(detfcstfile)
        det_fcst=dset.copy()
        dset.close()

        probfcstfile="{}/output/MME_probabilistic_forecast_{}.nc".format(str(fcstdir), season_params["fyear"])
        dset=xr.open_dataset(probfcstfile)
        pr_fcst=dset.copy()
        dset.close()


        dethcstfile="{}/output/MME_deterministic_hindcasts.nc".format(str(fcstdir))
        dset=xr.open_dataset(dethcstfile)
        det_hcst=dset.copy()
        dset.close()

        probhcstfile="{}/output/MME_probabilistic_hindcasts.nc".format(str(fcstdir))
        dset=xr.open_dataset(probhcstfile)
        pr_hcst=dset.copy()
        dset.close()

        dset=xr.open_dataset(predictandfile)
        ncvar=obs_ncvars[predictand_name][0]
        Y=dset[ncvar]
        dset.close()

        calibrated=True
            
    #defining directory to store maps
    mapdir="{}/{}/{}/{}/{}".format(maprootdir,basetime,predictand_domain,predictand_var,season_params["fdate"].strftime("%Y%m"))
    print("\nMap files will be stored in {}".format(mapdir))

    if not os.path.exists(mapdir):
        print("creating directory: {}".format(mapdir))
        os.makedirs(mapdir, exist_ok=True)

    #catching possible errors... 
    if skill_mask_code not in skillmasks.keys():
        print("ERROR: There is no entry for requested skill mask code in skillmasks dictionary: {}".format(skill_mask_code))
        sys.exit()

    #wrapping source label in case it is too long to fit below the frame of the figure
    sourcelabel=source+" ("+", ".join([x[0] for x in ensemblemembers])+")"
    sourcelabel="\n".join(textwrap.wrap(sourcelabel,70))

    for metric in fcst_outputs_to_plot:
        for do_mask, mask_label in skillmasks[skill_mask_code]: 
            print("\nchecking {}{} ...".format(metric, mask_label))
        

            mapfile="{}/{}_{}{}_{}_{}_{}.jpg".format(mapdir,predictand_var, metric,mask_label,mmecode,season_params["initdate"], season_params["target_seas"])

            if metric in ["det","det-absanom","det-relanom"]:
                fcstdata=det_fcst.copy()
            else:
                fcstdata=pr_fcst.copy()

            if (not os.path.exists(mapfile)) or overwrite:
                print("plotting {}...".format(mapfile))
                fun.plot_forecast(
                   predictand_category,
                   fcstdata,
                   nextgen_skill,
                   Y,
                   metric,
                   fcstvar_label,
                   basetime,
                   season_params["target_year_label"], 
                   target_seas,
                   season_params["initdate_label"],
                   predictand_dataset_label, 
                   first_hindcast_year,
                   last_hindcast_year,
                   overlayfile,
                   mapfile,
                   sourcelabel,
                   do_mask)
                print("written {}".format(mapfile))
            else:
                print("map file exists. skipping...")

    for metric in skill_metrics_to_plot:
        for do_mask, mask_label in skillmasks[skill_mask_code]: 
            print("\nchecking {}{} ...".format(metric, mask_label))        

            mapfile="{}/{}_{}{}_{}_{}_{}.jpg".format(mapdir,predictand_var, metric,mask_label,mmecode,season_params["initdate"], season_params["target_seas"])
            if (not os.path.exists(mapfile)) or overwrite:
                print("Plotting...")
                
                fun.plot_forecast(
                   predictand_var,
                   fcstdata,
                   nextgen_skill,
                   Y,
                   metric,
                   fcstvar_label,
                   basetime,
                   season_params["target_year_label"], 
                   target_seas,
                   season_params["initdate_label"],
                   predictand_dataset_label,
                   first_hindcast_year,
                   last_hindcast_year,
                   overlayfile,
                   mapfile,
                   sourcelabel,
                   do_mask)
                print("written {}".format(mapfile))
            else:
                print("map file exists. skipping...")


print("all done")







