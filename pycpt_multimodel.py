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

#file with sadc country boundaries to be overlaid on maps
overlayfile="../csis/gis/sadc_continental.geojson"

predictor_domain_file="./dictionaries/predictor_domains.json"
predictand_domain_file="./dictionaries/predictand_domains.json"

#location of logo image
logofile="../csis/img/csclogo-small.png"

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
sel_skill_metrics = [
        "rank_probability_skill_score",
        "generalized_roc",
        "spearman",
        "pearson",
        "two_alternative_forced_choice"
]

#these forecast metrics will be plotted
#these names are "bespoke", implemented in this script only, they are not "native" to pycpt
#defined as a function of predictand 
if predictor_var=="PRCP":
    sel_fcst_outputs=["deterministic",
        "deterministic-absanom",
        "deterministic-percanom",
        "probabilistic-tercile"]
else:
    sel_fcst_outputs=["deterministic",
        "deterministic-absanom",
        "probabilistic-tercile"]

#this defines predictands that will be read locally and not downloaded from IRI
local_predictands=["ERA5.TMEAN"]

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
   

skill_metric_params={
 'pearson':["Pearson's correlation","pearson",-1,1,10,"neither","BrBG",0.5,1,10,"neither","Blues", "less than"],
 'spearman':["Spearman's correlation","spearman",-1,1,10,"neither","BrBG",0.5,1,10,"neither","Blues", "less than"],
 '2afc':["2AFC score","2acf",0,100,10,"neither","BrBG",30,100,7,"neither","Blues", "less than"],
 "roc_area_below_normal":["ROC score for below normal",'rocbelow',0,100,10,"neither","BrBG",60,100,8,"neither","Blues", "less than"],
 "roc_area_above_normal":["ROC scoare for above normal",'rocabove',0,100,10,"neither","BrBG",60,100,8,"neither","Blues", "less than"],
 "generalized_roc":["Generalized ROC",'genroc',0,100,10,"neither","BrBG",60,100,8,"neither","Blues", "less than"],
 "rank_probability_skill_score":["Rank Probability Skill Score (RPSS)",'rpss',-100,100,10,"neither","BrBG",20,100,8,"neither","Blues", "less than"]
}

#this gives short names for forecast metrics to be used in naming output files
fcst_output_params={"deterministic":["det","spearman"],
        "deterministic-absanom":["det-absanom","spearman"],
        "deterministic-percanom":["det-percanom","spearman"],
        "probabilistic-tercile":["prob-terc","generalized_roc"]}

units={"PRCP":"mm/season",
        "TMEAN":"degC",
        "TMIN":"degC",
        "TMAX":"degC"}

labels={"UCSB.PRCP":"CHIRPS",
	"UCSB.TMEAN":"CHIRTS",
	"ERA5.TMEAN":"ERA5",
	"PRCP":"rainfall",
	"TMAX":"maximum temperature",
	"TMIN":"minimum temperature",
	"TMEAN":"mean temperature",
	"T2m":"mean temperature",
	}

obs_ncvars={"UCSB.PRCP":"prcp",
	"UCSB.TMEAN":"tmean",
	"ERA5.TMEAN":"TMEAN"
	}

#this sets up whether plotting is done with and/or without mask
skillmasks={"no":[[False,""]],
"yes":[[True,"-m"]],
"both":[[False,""], [True,"-m"]]}



   
# ============================================================================================
# picking up parameters for the requested forecast
#

#domain parameters
#predictor_domain_params = get_domain_params(predictor_domain_file,predictor_domain)
#predictand_domain_params = get_domain_params(predictand_domain_file,predictand_domain)
predictand_name="{}.{}".format(predictand_institution,predictand_var)



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


#catching possible errors... 
if skill_mask_code not in skillmasks.keys():
    print("ERROR: There is no entry for requested skill mask code in skillmasks dictionary: {}".format(skill_mask_code))
    sys.exit()

masks_to_plot=skillmasks[skill_mask_code]


    
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

predictand_name="{}.{}".format(predictand_institution,predictand_var)

#iterating through lead times
#for lead_time in leadtimes[basetime]:
for lead_time in [0]:
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
        print("predictand name: {}".format(predictand_name))

        if predictand_name in local_predictands:
            # internal parameter of pycpt - if set, then local file is used as predictand
            local_predictand_file = "{}/{}/{}/{}/{}_{}_{}.tsv".format(localpredictandrootdir,predictand_institution,basetime,predictand_domain,predictand_var,basetime, target_seas)
            print("using local predictand {}".format(local_predictand_file))
            
            if not os.path.exists(local_predictand_file):
                print("ERROR: Local predictand file does not exist: {}".format(local_predictand_file))
                sys.exit()
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
            print("ERROR. Could not find predictor {}".format(predictor_name))
            sys.exit()
            
        #checking if root directory exists
        if not os.path.exists(fcstrootdir):
            print("ERROR. Root directory does not exist {}".format(fcstrootdir))
            sys.exit()
            
        #this is definition of source directory

        memberrootdir="{}/forecast/{}".format(datadir,model)
        case_dir = "{}/{}/{}/{}/{}-{}/{}".format(memberrootdir,
                                     basetime,
                                     predictand_domain,
                                     predictand_var,
                                     season_params["fdate"].strftime("%Y%m"),
                                     target_seas,
                                     predictor_domain)
        # In[14]:


        inputdir="{}/output".format(case_dir)
        predictanddir="{}/data".format(case_dir)

        # checking overwrite
        inputfcstfile="{}/{}_realtime_{}_forecasts.nc".format(str(inputdir), predictor_name, MOS.lower())
        inputhcstfile="{}/{}_crossvalidated_{}_hindcasts.nc".format(str(inputdir), predictor_name, MOS.lower())
        predictandfile="{}/{}.nc".format(str(predictanddir), predictand_name)

        if not os.path.exists(inputfcstfile):
            print("ERROR. forecast file does not exist, but required {}".format(inputfcstfile))
            sys.exit()
        if not os.path.exists(inputhcstfile):
            print("ERROR. hindcast file does not exist, but required {}".format(inputhcstfile))
            sys.exit()
        if not os.path.exists(predictandfile):
            print("ERROR. predictand file does not exist, but required {}".format(predictandfile))
            sys.exit()

        fcst=xr.open_dataset(inputfcstfile)
        hcst=xr.open_dataset(inputhcstfile)
        fcsts.append(fcst)
        hcsts.append(hcst)

        ensemble.append(predictor_name)
        predictor_names.append(predictor_name)

    ncvar=obs_ncvars[predictand_name]
    Y=xr.open_dataset(predictandfile)[ncvar]

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

    if overwrite or (not os.path.exists(fcstfile)):
        print("processing forecast to {}".format(fcstfile))
        det_fcst, pr_fcst, pev_fcst, nextgen_skill = pycpt.construct_mme(fcsts, hcsts, Y, ensemble, predictor_names, cpt_args, fcstdir)
        #hcsts, fcsts, skill, pxs, pys = pycpt.evaluate_models(hindcast_data, MOS, Y, forecast_data, cpt_args, domain_dir, [predictor_name], interactive)
        calibrated=True
        print("done")
    else:
        calibrated=False
        print("forecast file {} exists. skipping calibration...".format(fcstfile)) 

    #sys.exit()
    # ============================================================================================


    # ============================================================================================
    # plotting figures
    #


    # ============================================================================================
    # this is not strictly necessary in operational, but can potentially be run if needed
    #
    #    if do_plot_eof_modes:
    #        pycpt.plot_eof_modes(MOS, [predictor_name], pxs, pys, domain_dir)

    #    if MOS=="CCA" and do_plot_cca_modes==True:
    #        pycpt.plot_cca_modes(MOS, [predictor_name], pxs, pys, domain_dir)


    #defining directory to store maps
    mapdir="{}/{}/{}/{}".format(maprootdir,basetime,predictand_domain,predictand_var)
    print("\nMap files will be stored in {}".format(mapdir))

    if not os.path.exists(mapdir):
        print("creating directory: {}".format(mapdir))
        os.makedirs(mapdir, exist_ok=True)



    #plotting skill scores defined in the sel_skill_metrics

    for metric in sel_skill_metrics:
        if metric not in skill_metric_params.keys():
            print("ERROR. Requested {} but only {} described in skill_metric_params".format(metric, ",".join(list(skill_metric_params.keys()))))
            sys.exit()
        metric_code=skill_metric_params[metric][1]

        for do_mask, mask_label in masks_to_plot:
           # skill-m_2acf_Sep-2024_SEAS51.SST.jpg
            #mapfile="{}/skill{}_{}-{}_{}_{}-{}.jpg".format(mapdir,mask_label, metric_code, predictor_name, predictor_domain, season_params["fdate"].strftime("%Y%m"), target_seas, season_params["target_year_label"].replace("/","-"))
            mapfile="{}/skill{}_{}_{}_{}_{}-{}.jpg".format(mapdir,mask_label, metric_code, mmecode, season_params["fdate"].strftime("%Y%m"), target_seas, season_params["target_year_label"].replace("/","-"))
            if (not os.path.exists(mapfile)) or overwrite:
                if not calibrated:
                    print("Opening forecast files...") 
                    skillfile="{}/output/MME_skill_scores.nc".format(str(fcstdir))
                    dset=xr.open_dataset(skillfile)
                    skill=[dset]
                    dset.close()

                    detfcstfile="{}/output/MME_deterministic_forecast_{}.nc".format(str(fcstdir),season_params["fyear"])
                    dset=xr.open_dataset(fcstfile)
                    det_fcst=[dset]
                    dset.close()

                    prfcstfile="{}/output/MME_probabilistic_forecast_{}.nc".format(str(fcstdir),season_params["fyear"])
                    dset=xr.open_dataset(fcstfile)
                    pr_fcst=[dset]
                    dset.close()


                    #hcstfile="{}/output/{}_crossvalidated_{}_hindcasts.nc".format(str(fcstdir), predictor_name, MOS.lower())
                    #dset=xr.open_dataset(hcstfile)
                    #hcsts=[dset]
                    #dset.close()

                    dset=xr.open_dataset(predictandfile)
                    ncvar=obs_ncvars[predictand_name]
                    Y=dset[ncvar]
                    dset.close()

                    calibrated=True

                print("Plotting...")

                #original pycpt function
                #pycpt.plot_skill([predictor_name], skill[0], MOS, domain_dir, [metric])

                #bespoke function
                fun.plot_skill(predictor_name,
                    skill[0],
                    MOS, 
                    metric,
                    fcstvar_label,
                    target_seas,
                    season_params["initdate_label"],
                    season_params["target_year_label"],
                    predictand_dataset_label,
                    first_hindcast_year,
                    last_hindcast_year,
                    overlayfile,
                    logofile,
                    mapfile,
                    do_mask,
                    skill_metric_params)
                print("saved {}...".format(mapfile))
            else:
                print("map file {} exists. skipping plotting...".format(mapfile)) 


    for fcst_output in sel_fcst_outputs:
        fcst_code=fcst_output_params[fcst_output][0]
        for do_mask, mask_label in masks_to_plot:
            # map file will be e.g. PRCP_prob-terc_SEAS51.SST-nino34_202405_MJJ-2024.jpg
            mapfile="{}/{}{}_{}_{}-{}_{}_{}-{}.jpg".format(mapdir,predictand_var,mask_label, fcst_code, predictor_name, predictor_domain, season_params["fdate"].strftime("%Y%m"), target_seas, season_params["target_year_label"].replace("/","-"))
            if (not os.path.exists(mapfile)) or overwrite:
                print("Plotting {}".format(mapfile)) 
                #opening files if necessary
                if not calibrated:
                    print("Opening forecast files...") 
                    skillfile="{}/output/{}_skillscores_{}.nc".format(str(domain_dir), predictor_name, MOS.lower())
                    dset=xr.open_dataset(skillfile)
                    skill=[dset]
                    dset.close()

                    fcstfile="{}/output/{}_realtime_{}_forecasts.nc".format(str(domain_dir), predictor_name, MOS.lower())
                    dset=xr.open_dataset(fcstfile)
                    fcsts=[dset]
                    dset.close()

                    hcstfile="{}/output/{}_crossvalidated_{}_hindcasts.nc".format(str(domain_dir), predictor_name, MOS.lower())
                    dset=xr.open_dataset(hcstfile)
                    hcsts=[dset]
                    dset.close()

                    dset=xr.open_dataset(predictand_file)
                    ncvar=obs_ncvars[predictand_name]
                    Y=dset[ncvar]
                    dset.close()

                    calibrated=True

                #original pycpt function 
                #pycpt.plot_forecasts(cpt_args, predictand_name, fcsts, domain_dir, [predictor_name], MOS)

                #bespoke function
                #
                fun.plot_forecast(predictor_name, 
                   fcsts[0],
                   skill[0],
                   Y,
                   MOS, 
                   season_params["target_year_label"], 
                   fcst_output, 
                   fcstvar_label,
                   target_seas, 
                   season_params["initdate_label"], 
                   predictand_dataset_label, 
                   first_hindcast_year,
                   last_hindcast_year,
                   units[predictand_var],
                   overlayfile,
                   logofile,
                   mapfile,
                   fcst_output_params[fcst_output][1],
                   skill_metric_params,
                   do_mask)

                print("saved {}...".format(mapfile))
            else:
                print("map file {} exists. skipping plotting...".format(mapfile)) 

print("all done")







