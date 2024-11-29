import numpy as np
import datetime as dt
import xarray as xr

from modules.string import string

def DigitalTwinProcess(jsondata, wms_data, instant_data):
    pass

    string_config = jsondata['string_config']
    
    string_vec = np.vectorize(string)

    string_current, string_voltage = string_vec(string_config, wms_data, instant_data)

    
    return string_current, string_voltage