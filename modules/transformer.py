from .cable import CableDrop
from .connector import ConnectorDrop
from .loss_bucketing import initiate_losses, compile_losses
from .performance import component_performance, component_efficiency

def TrafoCableConnectorDrop(input_current, input_voltage, cable_config, connector_config, ambient_temp):
    if cable_config is not None:
        cable_drop = CableDrop(cable_config, ambient_temp, input_current)
    else:
        cable_drop=0
    if connector_config is not None:   
        connector_drop = 2 * ConnectorDrop(connector_config, input_current, ambient_temp)
    else:
        connector_drop=0
    trafo_input_voltage = input_voltage - (cable_drop + connector_drop)
    trafo_input_current = input_current
    
    return trafo_input_current, trafo_input_voltage

def trafo_core_resis_correction_factor(trafo_config=None):
    # Need to add function for material
    return 234.5

def TransformerMain(input_current, input_voltage, transformer_config, ambient_temp):
    import math

    trafo_config, cable_config, connector_config = transformer_config['trafo'], transformer_config['cable'], transformer_config['connector']

    # Data required
    trafo_rating = trafo_config['rated_power']
    trafo_resis_cf = trafo_core_resis_correction_factor(trafo_config)
    trafo_res_thermal_coeff = trafo_config['thermal_coeff']
    trafo_winding_ratio = trafo_config['winding_ratio'] # winding ratio = primary turns / secondary turns. Here, low-turns /high-turns

    # Step 1: Adjusting input current and input voltage
    input_current, input_voltage = TrafoCableConnectorDrop(input_current, input_voltage, cable_config, connector_config, ambient_temp)
    
    trafo_input_power = math.sqrt(3) * input_current * input_voltage
    
    #Step 2:
    nl_losses, lvres, hvres = (
    trafo_config["fixedLosses"],
    trafo_config["lvResistance"],
    trafo_config["hvResistance"] 
    )

    fixedlosses_abienttemp, lvres_ambtemp, hvres_ambtemp = (
        (nl_losses * ((trafo_resis_cf + 75) / (trafo_resis_cf + (55 + ambient_temp)))),
        lvres * (1 + (trafo_res_thermal_coeff * (ambient_temp - 20))),
        hvres * ((trafo_resis_cf + (55 + ambient_temp)) / (trafo_resis_cf + 75)),
    )
    
    # Assuming the transformer output voltage
    trafo_output_voltage = input_voltage / trafo_winding_ratio

    if lvres_ambtemp != 0:
        transformer_copperlosses = input_voltage **2 / lvres_ambtemp 
    else:
        transformer_copperlosses = 0
    
    if hvres_ambtemp != 0:
        transformer_copperlosses += trafo_output_voltage**2 / hvres_ambtemp
    else:
        transformer_copperlosses += 0

    total_transformer_losses = fixedlosses_abienttemp + transformer_copperlosses

    transformer_eff = (
        (trafo_input_power - total_transformer_losses ) / trafo_input_power 
        if trafo_input_power > total_transformer_losses 
        else .9 #This might need to be changed.
    )
    
    trafo_output_power = transformer_eff * trafo_input_power

    trafo_output_current = trafo_output_power / math.sqrt(3) / trafo_output_voltage
    
    trafo_output = {
        'c': round(trafo_output_current, 6) if round(trafo_output_current, 3)==0.000 else round(trafo_output_current, 3), 
        'v': round(trafo_output_voltage, 3), 
        'p': round(trafo_output_power/1000, 3), 
        # 'rated_power': trafo_rating, 
        'eff': round(transformer_eff, 3), 
        # 'perf': component_performance(transformer_eff)
    }

    trafo_losses = initiate_losses()
    trafo_losses['fl'] += round(fixedlosses_abienttemp/1000, 3) 
    trafo_losses['tcl'] += round(transformer_copperlosses/1000, 3) 
    trafo_losses['ttl'] += round(total_transformer_losses/1000, 3)

    return trafo_output, trafo_losses