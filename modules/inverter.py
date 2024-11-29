from .cable import CableDrop, OhmicLoss
from .connector import ConnectorDrop
from .loss_bucketing import initiate_losses, compile_losses
from .performance import component_efficiency, component_performance

def InverterCableConnectorDrop(string_agg_current, string_agg_voltage, cable_config, connector_config, ambient_temp):

    if cable_config is not None:
        inv_cable_drop = CableDrop(cable_config, ambient_temp, string_agg_current)
    else:
        inv_cable_drop = 0

    if connector_config is not None:
        inv_connector_drop = ConnectorDrop(connector_config, string_agg_current, ambient_temp)
    else:
        inv_connector_drop = 0

    inv_input_voltage = string_agg_voltage - (inv_cable_drop + inv_connector_drop)
    
    return string_agg_current, inv_input_voltage

def pdc_degradation(input_dc_power, dc_degradation_value=0):
    return input_dc_power * (100 - dc_degradation_value)/100

def inverter_loading(input_dc_power, inv_rating, dc_degradation_value=0):
    pdc = pdc_degradation(input_dc_power, dc_degradation_value)
    return pdc/inv_rating*100

def pg_inverter(input_dc_power, ambient_temp, dc_degradation_value=0):
    #pdc must be in kW as per Uma's documentation.
    pdc = pdc_degradation(input_dc_power, dc_degradation_value)
    # Return only pdc values greater than 0.
    if ambient_temp <= 25:
        return pdc if pdc >= 0 else 0
    elif ambient_temp <= 50:
        pdc_ = (pdc/1000 + 2.*(25-ambient_temp))*1000
        return pdc_ if pdc_ >= 0 else 0
    elif ambient_temp <= 55:
        pdc_ = (pdc/1000 - 50 + 20*(50-ambient_temp))*1000
        return pdc_ if pdc_ >= 0 else 0
    else:
        pdc_ = (pdc/1000 - 150 + 82*(55-ambient_temp))*1000
        return pdc_ if pdc_ >= 0 else 0

def inv_efficiency(input_dc_power, inv_rating, dc_degradation_value=0):
        
    inv_loading = inverter_loading(input_dc_power, inv_rating, dc_degradation_value)

    if inv_loading < 20:
        efficiency = 97.5 + 0.025*inv_loading
    elif inv_loading < 30:
        efficiency = 98 + (0.02*(30-inv_loading))
    elif inv_loading < 40:
        efficiency = 98.2 + (-0.015*(40-inv_loading))
    elif inv_loading < 60:
        efficiency = 98.05 + (-0.0075*(60-inv_loading))
    elif inv_loading < 70:
        efficiency = 97.9 + (-0.005*(70-inv_loading))
    elif inv_loading < 80:
        efficiency = 97.7 + (-0.01*(80-inv_loading))
    elif inv_loading < 90:
        efficiency = 97.6 + (-0.0005*(90-inv_loading))
    elif inv_loading < 100:
        efficiency = 97.595 + (-0.0025*(100-inv_loading))
    else:
        efficiency = 97.594 + (-0.0001*(110-inv_loading))
                                                                                                                                                       
    return efficiency/100

def inverter_pac(input_dc_power, ambient_temp, inv_rating, dc_degradation_value=0):
    efficiency = inv_efficiency(input_dc_power, inv_rating, dc_degradation_value)
    pout = pg_inverter(input_dc_power, ambient_temp, dc_degradation_value)

    return efficiency*pout, efficiency, pout

def inv_oversizing(pac, inv_rating, oversizing_factor = 1.3):
    pwr_threshold = oversizing_factor * inv_rating

    if pac > pwr_threshold:
        pac_ = pwr_threshold
        oversizing_loss = pac - pac_
    else:
        pac_ = pac
        oversizing_loss = 0

    return pac_, oversizing_loss

#def clipped_ac(pac, total_inv_power):
#    clipping_threshold = 1.3*total_inv_power
#
#    if pac > clipping_threshold:
#        return clipping_threshold
#    else:
#        return pac
#
#def clipping_losses(pac, total_inv_power):
#    clipping_threshold = 1.3*total_inv_power
#
#    if pac > clipping_threshold:
#        return pac - clipping_threshold
#    else: 
#        return 0
#

def InverterMain(string_agg_current, string_agg_voltage, inverter_config, ambient_temp):
    
    import math

    inverter, cable_config, connector_config = inverter_config['inverter'], inverter_config['cable'], inverter_config['connector']

    # Data required
    inv_rating = inverter['rated_power'] * 1000 # Rating in data in kW
    inv_ac_voltage = inverter['rated_vlt']
    oversizing_factor = 1.3
    dc_degradation_value = 3

    #Calculations
    dc_input_current, dc_input_voltage = InverterCableConnectorDrop(string_agg_current, string_agg_voltage, cable_config, connector_config, ambient_temp)
    
    dc_input_power = dc_input_current * dc_input_voltage

    # dc_degradation value changed to zero as per Uma's latest documentation.
    pac, efficiency, temp_adjusted_dc_pwr = inverter_pac(dc_input_power, ambient_temp, inv_rating, dc_degradation_value)
    pac=pac#/1000

    # Inverter oversizing losses
    pac, inv_oversizing_loss = inv_oversizing(pac, inv_rating, oversizing_factor = oversizing_factor)

    pac_virtual_inv = round(dc_input_power / oversizing_factor / 1000, 3) # As requested by Kumar. Virtual inv output in kW.

    inv_ac_current = pac / (math.sqrt(3) * inv_ac_voltage)
    
    inv_output = {
        'c': round(inv_ac_current, 3), 
        'v': round(inv_ac_voltage, 3), 
        'p': round(pac/1000, 3),    #convert it to kW
        'p_dc': round(dc_input_power/1000,3), #converted to kW
        'p_virtual': pac_virtual_inv, # Virtual inverter power as requested by Kumar.
        # 'rated_power': inv_rating, 
        # 'rated_voltage': inv_ac_voltage, 
        'eff': round(efficiency, 3),
        # 'perf': component_performance(efficiency)
    }

    # All losses at inv level are converted to AC losses.
    inv_losses = initiate_losses()
    inv_losses['ol'] += round(OhmicLoss(cable_config, ambient_temp, string_agg_current) * efficiency/1000, 3)
    inv_losses['tl'] += round((temp_adjusted_dc_pwr - dc_input_power) * efficiency/1000, 3) 
    inv_losses['osl'] += round(inv_oversizing_loss/1000, 3)

    # inv_losses = {
    #     'ohmicloss': OhmicLoss(cable_config, ambient_temp, string_agg_current) * efficiency, 
    #     'temperatureloss': (temp_adjusted_dc_pwr - dc_input_power) * efficiency, 
    #     'oversizingloss': inv_oversizing_loss
    # }

    return inv_output, inv_losses
