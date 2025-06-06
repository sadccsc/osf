import xarray as xr
import geopandas
import matplotlib.colors as colors
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import geojson
import os, sys, glob
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from functions_pycpt import *

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
seasons=["JFM","FMA","MAM","AMJ","MJJ","JJA","JAS","SON","OND","NDJ","DJF"]
# there are two sets of color maps - one for the entire range of skill values, and one when skill is masked

#location of logo image
logofile="./img/csclogo-small.png"

#dictionaries
units_file="./dictionaries/units.json"
labels_file="./dictionaries/labels.json"
fcst_metric_params_file="./dictionaries/fcst_metric_params.json"
skill_metric_params_file="./dictionaries/skill_metric_params.json"

units=parse_json(units_file)
labels=parse_json(labels_file)

onsetdefs={
    "onsetA":["25 mm of accumulated rainfall in 10 days","Tadross et al. 2007"],
    "onsetB":["25 mm of accumulated rainfall in 10 days, \nnot followed by a period of 10 consecutive days with observed rainfall < 2 mm in the following 20 days","??"],
    "onsetC":["45 mm of accumulated rainfall in 4 days","??"],
    "onsetD":["20mm threshold over 3 days and no dry spell in the next 10 days","??"]
}


accumdefs={
    "seasaccum":{"summer":"Accumulation since the 1st of July"},
    "onset":{"summer": "Calculated after the 1st of September"}
}


# in this dictionary, for consistency with skill_metric_params, there are two sets of color maps, but they should be identical, because colour maps do not change when masking for skill
fcst_metric_params=parse_json(fcst_metric_params_file)
skill_metric_params=parse_json(skill_metric_params_file)


def plot_forecast(_predictand_category, _predictand_var, _fcstdata, _skilldata, _obsdata,_metric, _basetime, _season_params, _predictand_dataset, _first_hindcast_year, _last_hindcast_year, _overlayfile,_mapfile, _fcst_model,_do_mask):
    #
    #
    #_metric is "internal" metric name used by this script and dictonaries. it is either a skill metric or forecast metric, i.e. one of det, det-abanom, det-percanom, prob-tercile. It is used to create meaningful file names.
    #_pycpt_metric_name - is name used in pycpt output files
    #_maskmetric - is the "internal" code for the metric that is used to mask the map
    #_pycpt_maskmetric_name - is name of the metric used in pycpt

    if _metric in skill_metric_params:
        _pycpt_metric_name=skill_metric_params[_metric][0]
    elif _metric in fcst_metric_params[_predictand_category].keys():
        _pycpt_metric_name=fcst_metric_params[_predictand_category][_metric][0]
    else:
        print("ERROR. Requested {} but only {} described in skill_metric_params and {} in fcst_metric_params".format(_metric, ",".join(list(skill_metric_params.keys())), ",".join(list(fcst_metric_params[_predictand_category].keys()))))
        sys.exit()
        
    if _metric=="clim" and _do_mask:
        print("we are not skill-masking climatology")
    else: 
        _metric_label=labels[_metric]
        _fcstvar_label=labels[_predictand_var]

        _predictand_dataset_label=labels[_predictand_dataset]
        _initdate_label=_season_params["initdate_label"]

        _annotation="Source: {} calibrated at SADC CSC".format(_fcst_model)
        _maskdata=None
        
        if _predictand_category in ["onset"]:
            _regime="summer"
            _annotation="{}\nDefinition: {}\n{}".format(_annotation, onsetdefs[_predictand_var][0], accumdefs[_predictand_category][_regime])
            
            _target_year_label=_season_params["target_rainy_season"]
            _target_seas=""        
        else:
            _target_year_label=_season_params["target_year_label"]
            _target_seas=_season_params["target_seas"]

           
            
        if _metric in ["det","det-absanom","det-percanom","prob-tercile", "clim"]:
            #this is for all forecast maps
            if _metric=="det":
                _data=_fcstdata["deterministic"].copy()
                _title="Deterministic forecast \nof {} in {} {}\nissued in {}".format(_fcstvar_label, _target_seas,_target_year_label, _initdate_label)

            elif _metric=="det-absanom":
                _data=_fcstdata["deterministic"].copy()-_obsdata.mean("T").data
                if _predictand_category=="onset":
                    #converting days to dekads
                    _data=_data/10
                _title="Deterministic forecast \nof {} in {} {} (absolute anomaly) \nissued in {}".format(_fcstvar_label, _target_seas,_target_year_label, _initdate_label)

            elif _metric=="det-percanom":
                _data=(_fcstdata["deterministic"].copy()-_obsdata.mean("T").data)/_obsdata.mean("T").data*100
                #overwriting the "general" value 
                _cbar_label="% anomaly"
                _title="Deterministic forecast \nof {} for {} {} (percent anomaly)\nissued in {}".format(_fcstvar_label, _target_seas,_target_year_label, _initdate_label)

            elif _metric=="prob-tercile":
                _data=_fcstdata["probabilistic"].copy()        
                _datamax=_data==_data.max("C")
                _data=_data.where(_datamax)
                _data[1,:]=_data[1,:]+200
                _data[2,:]=_data[2,:]+400
                _data=_data.max("C")
                _title="Probabilistic (tercile) forecast\nof {} for {} {}\nissued in {}".format(_fcstvar_label, _target_seas,_target_year_label, _initdate_label)

            elif _metric=="clim":
                _data=_obsdata.mean("T")
                if _predictand_category=="onset":
                    _title="Climatology of {}\n(over {}-{})".format(_fcstvar_label,  _first_hindcast_year, _last_hindcast_year)
                else:
                    _title="Climatology of {}\n(over {}-{})".format(_fcstvar_label, _target_seas,_first_hindcast_year, _last_hindcast_year)
                    
            #common for all forecast metrics
            _plotparams=get_plotparams(_data, _metric, _do_mask, fcst_metric_params[_predictand_category],_predictand_category)
            if _predictand_category=="onset" and _metric in ["det-absanom"]:
                 _cbar_label="    dekads early     dekads late"
            else:
                _cbar_label=units[_predictand_category]
            _maskmetric=fcst_metric_params[_predictand_category][_metric][11]
            _pycpt_maskmetric_name=skill_metric_params[_maskmetric][0]

        else:
            #this is for all skill maps
            _data=_skilldata[_pycpt_metric_name].copy()
            _plotparams=get_plotparams(_data, _metric, _do_mask,skill_metric_params,_predictand_category)
            _title="Forecast skill ({})\nfor forecast of {} in {} {}\nissued in {}".format(_metric_label, _fcstvar_label, _target_seas,_target_year_label, _initdate_label)
            # skill will be masked by itself
            _maskmetric=_metric
            _pycpt_maskmetric_name=skill_metric_params[_maskmetric][0]
            _cbar_label="score"
            
            
        if _do_mask:
            print("masking...")
            _maskdata=_skilldata[_pycpt_maskmetric_name].copy()
            _masktype=skill_metric_params[_maskmetric][12]
            _maskmetric_label=labels[_maskmetric]
            #might need expanding, if there is a need to have a different mask some time in the future 
            if _masktype=="less than":
                _thresh=skill_metric_params[_maskmetric][13]
                _maskdata=_maskdata>_thresh
                _signlabel="less than {}".format(_thresh)
            else:
                #might need expanding if other types are necessary
                print("Only less than accepted as masktype at the moment. requested {}. exiting...".format(_masktype))
                cont=True
                sys.exit()
            #adding skill mask info to annotation
            _annotation="{}\nSkill evaluated by {} against {} data over {}-{} period".format(_annotation,_metric_label, _predictand_dataset_label, _first_hindcast_year,_last_hindcast_year)
            _annotation="{}\nValues where {} is {} are masked out".format(_annotation,_maskmetric_label,_signlabel)
            
            #implementing mask
            _data=_data.where(_maskdata)

        print("plotting map")

        plot_map(_data,
                     _plotparams["cmap"],
                     _plotparams["vmin"],
                     _plotparams["vmax"],
                     _plotparams["levels"],
                     _plotparams["ticklabels"],
                     _plotparams["norm"],
                     _plotparams["extend"],
                     _cbar_label,
                     _title,
                     _annotation,
                     _maskdata,
                     _metric,
                     _predictand_category,
                     _predictand_var,
                     _mapfile, 
                     _overlayfile,
                     logofile,
                     _plotbackground=False)





def plot_map(_data,_cmap,_vmin,_vmax,_levels,_ticklabels,_norm, _extend, _cbar_label,_title, _annotation,_maskdata, _metric, _predictand_category,_predictand_var, _filename, _overlayfile, _logofile, _plotbackground=False):
    
    _clip=False
    if _overlayfile: 
        overlay = geopandas.read_file(_overlayfile)
        _clip=True


    fig=plt.figure(figsize=(5,5))
    pl=fig.add_subplot(1,1,1, projection=ccrs.PlateCarree())
    
    if _maskdata is not None:
        _data=_data.where(_maskdata)

    if _clip:
       # print(_data)
        #clip grid to polygon
        _data=_data.rio.write_crs("epsg:4326")
        _data.rio.set_spatial_dims("X","Y")
        _data=_data.rio.clip(overlay.geometry.values, "epsg:4326")

    if _metric=="prob-tercile":
        if _predictand_category=="onset":
            _cmap_above="BrBG_r"
            _cmap_below="BrBG"
        elif _predictand_category=="rainfall":
            if _predictand_var=="Rx5day":
                _cmap_above="BrBG_r"
                _cmap_below="BrBG"
            else:
                _cmap_above="BrBG"
                _cmap_below="BrBG_r"
        else:
            _cmap_above="RdYlBu_r"
            _cmap_below="RdYlBu"
            
        if _predictand_category =="onset":
            cbar_label_dry="probablity [%]\nearlier\nthan normal"
            cbar_label_norm="probablity [%]\nnormal"
            cbar_label_wet="probablity [%]\nlater\nthan normal"
        else:
            cbar_label_dry="probablity [%]\nbelow normal"
            cbar_label_norm="probablity [%]\nnormal"
            cbar_label_wet="probablity [%]\nabove normal"
            
        levels_dry=[33,40,50,60,70,100]
        ncat=len(levels_dry)
        cmap_dry = plt.get_cmap(_cmap_below)
        cols_dry = cmap_dry(np.linspace(0.5, 0.9, ncat-1))
        cmap_dry, norm_dry = colors.from_levels_and_colors(levels_dry, cols_dry, extend="neither")
        m_dry=_data.plot(cmap=cmap_dry, vmin=33,vmax=100, add_colorbar=False, norm=norm_dry, ax=pl)


        levels_norm=[233,240,250,270,300]
        ncat=len(levels_norm)
        cmap_norm = plt.get_cmap("Greys")
        cols_norm = cmap_norm(np.linspace(0, 0.5, ncat-1))
        cmap_norm, norm_norm = colors.from_levels_and_colors(levels_norm, cols_norm, extend="neither")
        m_norm=_data.plot(cmap=cmap_norm, vmin=233,vmax=300, add_colorbar=False, norm=norm_norm, ax=pl)

        levels_wet=[433,440,450,460,470,500]
        ncat=len(levels_wet)
        cmap_wet = plt.get_cmap(_cmap_above)
        cols_wet = cmap_wet(np.linspace(0.5, 0.9, ncat-1))
        cmap_wet, norm_wet = colors.from_levels_and_colors(levels_wet, cols_wet, extend="neither")
        m_wet=_data.plot(cmap=cmap_wet, vmin=433,vmax=500, add_colorbar=False, norm=norm_wet, ax=pl)
        
        
        #legends
        ax=fig.add_axes([0.82,0.25,0.02,0.15])
        cbar = fig.colorbar(m_dry, cax=ax,ticks=levels_dry, extend="neither")
        _ticklabels=levels_dry
        cbar.set_label(cbar_label_dry, fontsize=8)
        cbar.ax.set_yticklabels(_ticklabels)
        cbar.ax.tick_params(labelsize=6)
        cbar.ax.tick_params(size=0)

        ax=fig.add_axes([0.82,0.45,0.02,0.1])
        cbar = fig.colorbar(m_norm, cax=ax,ticks=levels_norm, label=cbar_label_norm, extend="neither")
        _ticklabels=levels_norm    
        cbar.set_label(cbar_label_norm, fontsize=8)
        cbar.ax.set_yticklabels([x-200 for x in _ticklabels])
        cbar.ax.tick_params(labelsize=6)
        cbar.ax.tick_params(size=0)

        ax=fig.add_axes([0.82,0.60,0.02,0.15])
        cbar = fig.colorbar(m_wet, cax=ax,ticks=levels_wet, label=cbar_label_wet, extend="neither")

        _ticklabels=levels_wet
        cbar.set_label(cbar_label_wet, fontsize=8)
        cbar.ax.set_yticklabels([x-400 for x in _ticklabels])
        cbar.ax.tick_params(labelsize=6)
        cbar.ax.tick_params(size=0)
        
    else:
        #this would be section for "normal" maps
        m=_data.plot(cmap=_cmap, vmin=_vmin,vmax=_vmax, add_colorbar=False, norm=_norm)
        
        ax=fig.add_axes([0.82,0.25,0.02,0.5])
        if _levels is None:
            cbar = fig.colorbar(m, cax=ax, label=_cbar_label, extend=_extend)
        else:
            cbar = fig.colorbar(m, cax=ax,ticks=_levels, label=_cbar_label, extend=_extend)

        if _ticklabels is not None:
            cbar.ax.set_yticklabels(_ticklabels)
            cbar.ax.tick_params(labelsize=8)
            cbar.ax.tick_params(size=0)
            cbar.set_label(_cbar_label, labelpad=-10)            
            
    pl.set_title(_title, fontsize=9)

    
    logoimg = plt.imread(_logofile)
    im = OffsetImage(logoimg, zoom=0.3)
    ab = AnnotationBbox(im, (0.99, 0.99), xycoords=pl.transAxes, box_alignment=(1,1), frameon=False)
    pl.add_artist(ab)

    
    #common to all maps
    
    if _plotbackground:
        overlay.plot(ax=pl, color="0.7")
    overlay.boundary.plot(ax=pl, linewidth=0.3, color="0.1")

    
    pl.text(0,-0.01,_annotation,fontsize=6, transform=pl.transAxes, va="top")
    
    plt.subplots_adjust(bottom=0.06,top=0.95,right=0.8,left=0.05)
    
    if _filename:
        plt.savefig(_filename, dpi=300)
    plt.close()
    

def get_cmap(_data, _cmap, _vmin,_vmax,_ncat,_centre, _extend):
    #this generates categorical colormap
    if _vmax=="auto":
        #if vmax is to be calculated automatically
        _vmax=np.nanquantile(_data, 0.95)
        _vmax=neat_vmax(_vmax,_ncat)
    if _vmin=="auto":
        #_vmin will be symmetrical around 0 to vmax
        _vmin=-_vmax
        
    _catwidth=(_vmax-_vmin)/_ncat
    _levels = np.round(np.arange(_vmin,1.01*_vmax,_catwidth), 2)
    
    if _extend=="both":
        _ncolors=len(_levels)+1
    elif _extend=="neither":
        _ncolors=len(_levels)-1
    else:
        _ncolors=len(_levels)
    
    _cmap_rb = plt.get_cmap(_cmap)    
    _cols = _cmap_rb(np.linspace(0.1, 0.9, _ncolors))
    _cmap, _norm = colors.from_levels_and_colors(_levels, _cols, extend=_extend)
    return({"cmap":_cmap, "levels":_levels, "vmin":_vmin, "vmax":_vmax,"ticklabels":None, "norm":_norm, "extend":_extend})


        
def get_plotparams(_data,_metric, do_mask,_params,_predictand_category):
    if( _predictand_category=="onset") & (_metric in ["det", "clim"]):
        _vmin,_vmax=0,180
        _cols= ["#224E96","#2E67AF","#4284C4","#59A3D7","#73BAE5","#8ECFF0","#8BBD9F","#A3C38F","#CBE0B7","#EAEFAA","#FBE884","#FDD76D","#FAB446","#F3692A","#E95029","#DE3828", "#C91E26","#B01A20","#921519"]
        _levels = [0,10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180]
        _cmap, _norm = colors.from_levels_and_colors(_levels, _cols, extend="max")
        _ticklevels = [0,30,60,90,120,150]
        _ticklabels=[ 'Sep', 'Oct', 'Nov', 'Dec', 'Jan',"Feb    ."]
        _units="dekad"
        _extend="max"
        paramdict={"cmap":_cmap, "levels":_ticklevels, "vmin":_vmin, "vmax":_vmax,"ticklabels":_ticklabels, "norm":_norm, "extend":_extend, "units":_units}
                            
    else:
        if _metric in _params.keys():
            plotvarCode,vmin,vmax,ncat,extend,cmap,mask_vmin,mask_vmax,mask_ncat,mask_extend,mask_cmap,maskvar,masktype,maskthresh=_params[_metric]
            #print(_metric,plotvarCode,vmin,vmax)
            if do_mask:
                paramdict=get_cmap(_data,mask_cmap,mask_vmin,mask_vmax,mask_ncat,None,mask_extend)
            else:
                paramdict=get_cmap(_data,cmap,vmin,vmax,ncat,None,extend)
        else:
            print("ERROR. {} not in parameter dictionary (get_plotparams())".format(_metric))
            sys.exit()
        
    return(paramdict)



def neat_vmax(_vmax,_ncat):
    #nominal step
    step=_vmax/_ncat
    nofzeros=np.floor(np.log10(step))
    #normalized step
    stepnorm=step/10**nofzeros #this will always be between 1 and 10
    #all possible steps
    allsteps=np.array([1,1.5,2,2.5,3,4,5,7.5,10])
    #how close is nominal step from normalized step
    xx=np.abs(allsteps-stepnorm)
    #selecting the closest step
    sel=np.where(xx==np.min(xx))[0][0]
    #final step
    finalstep=allsteps[sel]
    
    finalvmax=finalstep*_ncat
    finalvmax=finalvmax*10**nofzeros
    return(finalvmax)
       




