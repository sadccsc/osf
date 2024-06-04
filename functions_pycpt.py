import pandas as pd
import calendar
import json,sys,os

def get_season_params(lead_time, init_date, basetime):
    months=[x for x in calendar.month_abbr][1:]
    if basetime=="seas":
        seasons=["JFM","FMA","MAM","AMJ","MJJ","JJA","JAS","ASO","SON","OND","NDJ","DJF"]
    else:
        seasons=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        
    #gives all parameters of forecast period that pycpt needs based on the initialization time and target season
    init_date=pd.to_datetime(init_date)
    init_mon=init_date.month
    init_year=init_date.year

    #getting starting month of the season
    target_mon=init_mon+lead_time #calendar month

    if target_mon>12:
        target_mon=target_mon-12
        
    target_seas=seasons[target_mon-1]
    
    lead_low = lead_time+0.5
    
    if basetime=="seas":
        nmon=2        
    else:
        nmon=0
    lead_high = lead_time+0.5+nmon
        
    #pycpt expression    
    target = "{}-{}".format(months[target_mon-1], (months*2)[target_mon-1+nmon])
    
    if target_mon<init_mon:
        yearexpr="{}/{}".format(init_year,int(init_year)+1)
        target_year=str(int(init_year)+1)
    else:
        yearexpr=str(init_year)
        target_year=str(init_year)

    initdate_label=init_date.strftime("%b %Y")
    initdate=init_date.strftime("%Y-%b")
    targetdate="{}{}01".format(target_year,str(target_mon).zfill(2))

    return {"fyear": init_year, "fdate": init_date,"target": target, "lead_low": lead_low, "lead_high":lead_high, "target_year_label":yearexpr, "initdate_label":initdate_label,"target_seas":target_seas, "initdate": initdate, "targetdate":targetdate, "leadtime":lead_time}
            

def parse_json(_jsonfile):
    if not os.path.exists(_jsonfile):
        print("ERROR. json file missing. {}".format(_jsonfile))
        sys.exit()
    else:
        with open(_jsonfile) as jf:
            adict= json.load(jf)
        return adict

def read_dict(_dict,_key,_label):

    if _key not in _dict.keys():
        print("ERROR: There is no entry for requested key {} in {} dictionary: {}".format(_key, _label))
        sys.exit()
    else:
         return _dict[_key]






def get_domain_params(domain_file, domain_name):
    if not os.path.exists(domain_file):
        print("ERROR. domain file missing. {}".format(domain_file))
        return False

    with open(domain_file) as json_file:
        domaindict= json.load(json_file)

    if domain_name not in domaindict.keys():
        print("ERROR. Requested extents for {}, but only {} available".format(domain_name, ", ".join(list(domaindict.keys()))))
        return False
    else:
        domain_data=domaindict[domain_name]
        return domain_data
