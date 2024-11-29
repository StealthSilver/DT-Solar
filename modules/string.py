from .cable import CableDrop, OhmicLoss
from .connector import ConnectorDrop, JointLoss
from .pv import PVModule
from .module_temperature import module_temperature
from .iam_losses import IncidanceAngleLosses
from .loss_bucketing import initiate_losses, compile_losses
from .performance import component_efficiency, component_performance

from datetime import date

# What is string configuration?
# It should include count and types of module.
# Cable and connector configuration
# What happens to string current when there is a module mismatch?
# Which module degrades due to mismatch, the one with lower or higher module current? 
# Degradation calculation due to module mismatch?
# string_config['modules'] = [ {'count':xx, 'module_key': xx_xx}, {'count':yy, 'module_key': yy_yy} ]
# string_config['cable'] = {'cable_length':xx, 'cable_resistance_per_meter':yy, 'cable_thermal_coeff':zz}
# string_config['connector'] = {'connector_resistance':xx, 'connector_thermal_coeff':yy}
# Global variable dict containing all PV module details based on a module_key
# module_global = {
#                   'module_key1':{'Vmp':xx, 'Imp':yy, 'KIsc':zz, 'KVoc':aa},
#                   'module_key2':{'Vmp':xx, 'Imp':yy, 'KIsc':zz, 'KVoc':aa}
#                   }
# wms_data = {
#               'poa':xx, 'wind_speed':yy, 'temperature':zz, 'poa_dw':aa    
#               }
# instant_data = {
#                   'startdata': xx, 'latitude':yy, 'tiltangle':zz, 'reftime':aa, 'azimuthalangle':bb
#                   }

module_global = {
                    'A1': {
                                'Vmp': 41.05, 'Imp': 10.84, 'KIsc': 0.035, 'KVoc': -0.28, 'bifacial': True 
                                },
                    'A2': {
                                'Vmp': 41.05, 'Imp': 10.84, 'KIsc': 0.035, 'KVoc': -0.28, 'bifacial': False 
                                }
                    }

def StringMain(string_config, wms_data, plant_data, rt_data=None):
    from datetime import datetime

    cable_config, connector_config, string_modules = string_config['cable'], string_config['connector'], string_config['modules']

    poa_dw, ambient_temp = wms_data['poa_dw'], wms_data['ambTemp']

    try:
        wind_speed = wms_data['windspeed']
    except:
        wind_speed = 10
    
    if 'poa' in wms_data.keys():
        poa = wms_data['poa']
    elif 'gti' in wms_data.keys():
        poa = wms_data['gti']
    else:
        poa = 0

    try:
        reftime = datetime.strptime(wms_data['planttimestamp'][:19], "%Y-%m-%dT%H:%M:%S") 
    except:
        reftime = wms_data['planttimestamp']

#Assume the minimum module current is the string current
    module_currents, module_voltages = [], []

    latitude, tiltangle, azimuthalangle = plant_data['latitude'], plant_data['tiltangle'], plant_data['azimuthangle']
    startdate = date(reftime.year, 1, 1)

    # Initiating string temperature and iam losses
    string_temploss, string_iamloss = 0, 0

    string_ratedpower, string_solarpower = 0, 0

    for module in string_modules:
        num_of_modules_in_string = module['count']

        # Vmp, Imp, KIsc, KVoc = (module_global[module['module_key']]['Vmp'], 
        #                         module_global[module['module_key']]['Imp'], 
        #                         module_global[module['module_key']]['KIsc'],
        #                         module_global[module['module_key']]['KVoc'] 
        #                         )
        Vmp, Imp, KIsc, KVoc = module['Vmp'], module['Imp'], module['KIsc'], module['KVoc']

        # if module_global[module['module_key']]['bifacial']:
        #     irradiation = (poa*1.0 + poa_dw*0.0)/1.0
        # else:
        #     irradiation = poa

        try:
            module_temp = wms_data['modTemp']
        except:
            module_temp = module_temperature(ambient_temp, wind_speed, poa)

        if module['bif'] is not None:
            irradiation = poa + poa_dw*module['bif'] # 0.7 is the bifaciality factor, csbpl has bifacial panels
        else:
            irradiation = poa

        irradiation = irradiation if irradiation >= 5. else 0
        
        fiam, corrected_irradiation = IncidanceAngleLosses(startdate, latitude, tiltangle, reftime, azimuthalangle, irradiation)

        module_current, module_voltage, module_temploss, module_iamloss = PVModule(Vmp, Imp, KVoc, KIsc, module_temp, corrected_irradiation, fiam)

        module_currents.append(module_current)
        module_voltages.append(module_voltage*num_of_modules_in_string)

        string_ratedpower += Vmp*Imp * num_of_modules_in_string
        string_solarpower += Vmp*Imp * num_of_modules_in_string * poa /1000 + module_temploss * num_of_modules_in_string

        string_temploss += module_temploss * num_of_modules_in_string
        string_iamloss += module_iamloss * num_of_modules_in_string

    string_current = min(module_currents)

    string_voltage = sum(module_voltages)

    if cable_config is None:
        module_to_module_cable_drop = 0
    else:
        module_to_module_cable_drop = CableDrop(cable_config, ambient_temp, string_current)

    if connector_config is None:
        module_to_connector_drop = 0
    else:
        module_to_connector_drop = ConnectorDrop(connector_config, string_current, ambient_temp)

    string_voltage = string_voltage - (num_of_modules_in_string - 1) * module_to_module_cable_drop - (2*num_of_modules_in_string - 1) * module_to_connector_drop

    string_power = string_current * string_voltage

    try:
        efficiency = component_efficiency(string_power, string_solarpower)
    except:
        efficiency = 0

    stringoutput = {
        "c": round(string_current, 3),
        "v": round(string_voltage, 3),
        "p": round(string_power/1000, 3), # power always in kW
        "rp": round(string_ratedpower/1000, 3), 
        "ip": round(string_solarpower/1000, 3), 
        "eff": efficiency,
        # "perf": component_performance(efficiency)
    }

    if rt_data is not None:
        if 'pwr' in rt_data.keys() and rt_data['pwr'] != 0:
            stringoutput['d'] = round((stringoutput['p'] - rt_data['pwr'])/rt_data['pwr'], 3)
            stringoutput['perf'] = component_performance(rt_data['pwr']/stringoutput['p'])
        else:
            stringoutput['d'] = 9999
            stringoutput['perf'] = component_performance(-1)
    else:
        stringoutput['d'] = 9999
        stringoutput['perf'] = component_performance(-1)
    
    stringlosses = initiate_losses()
    stringlosses['il'] += round(string_iamloss/1000, 3)
    stringlosses['tl'] += round(string_temploss/1000, 3)
    stringlosses["ol"] += round(((num_of_modules_in_string - 1) * module_to_module_cable_drop * string_current)/1000, 3)
    stringlosses["jl"] += round(((2*num_of_modules_in_string - 1) * module_to_connector_drop * string_current)/1000, 3)

    # stringlosses = {
    #     # "operationloss": string_ratedpower - string_power,
    #     # "solarloss": string_ratedpower - string_solarpower,  
    #     "temperatureloss": string_temploss,
    #     "iamloss": string_iamloss,
    #     "ohmicloss": (num_of_modules_in_string - 1) * module_to_module_cable_drop * string_current,
    #     "jointloss": (2*num_of_modules_in_string - 1) * module_to_connector_drop * string_current,
    # }

    # stringlosses['recoverable'] = stringlosses['ohmicloss'] + stringlosses['jointloss']
    # stringlosses['irrecoverable'] = stringlosses['iamloss'] + stringlosses['temperatureloss']
    
    return stringoutput, stringlosses        
