import numpy as np
import warnings
from .loss_bucketing import initiate_losses, compile_losses
from .performance import component_efficiency, component_performance

# Iterating over the strings connected to an scb. 
# # Gives the input of a single scb containing strings.
def string_iterator(pv_string_data, wmsdata, plant_specific_data, pvstring_rt=None):
    from modules.string import StringMain

    stringcurrents, stringvoltages = [], []
    stringpowers, stringratedpowers, stringidealpowers = [], [], []

    pvStrings = []
    stringcombinerlosses = initiate_losses()
    string_iterator_output = {
        'deviceid': pv_string_data['deviceid'], 
        # 'devicename': pv_string_data['devicename'],
        'isDeleted': pv_string_data['isDeleted'], 
        # 'isscb': pv_string_data['isscb'], 
        'o': None, 'cuml': None, 
        # 'pvStrings': None # Commented since we removed it below as well for storing reasons.
    }

    if 'poa' in wmsdata.keys():
        poa = wmsdata['poa']
    elif 'gti' in wmsdata.keys():
        poa = wmsdata['gti']
    else:
        poa = 0

    for stringindex, string in enumerate(pv_string_data['pvStrings']):

        if (pvstring_rt is not None) and 'pvStrings' in pvstring_rt.keys():
            rt_data_sub = pvstring_rt['pvStrings'][stringindex]
        else:
            rt_data_sub = None 

        string_info = {}
        # string_info['stringname'] = string['stringname']
        string_info['isDeleted'] = string['isDeleted']

        if string['isDeleted'] is False:
            if 'cableConfig' not in string.keys():
                cable_config = None
            else:
                cable_config = string['cableConfig']

            if 'connectorConfig' not in string.keys():
                connector_config = None
            else:
                connector_config = string['connectorConfig']

            string_module_config = []
            module_config = {}
            module_config['count'] = string['modConnected']
            module_config['Vmp'] = string['pvModule']['vmp']
            module_config['Imp'] = string['pvModule']['imp']
            module_config['KVoc'] = string['pvModule']['kvoc']
            module_config['KIsc'] = string['pvModule']['kisc']
            # Currently hard coded bif for csbpl. needs to be read from the config json file.
            module_config['bif'] = string['pvModule']['bif'] if (string['pvModule']['bif'] is not None) else 0.70
            
            string_module_config.append(module_config)

            string_config = {}
            string_config['cable'] = cable_config
            string_config['connector'] = connector_config
            string_config['modules'] = string_module_config

            stringoutput, stringlosses = StringMain(string_config, wmsdata, plant_specific_data, rt_data_sub)
            # stringoutput['losses'] = stringlosses
            string_info['o'] = stringoutput
            string_info['cuml'] = stringlosses

            stringcombinerlosses = compile_losses(stringcombinerlosses, stringlosses)

            stringcurrents.append(stringoutput['c'])
            stringvoltages.append(stringoutput['v'])
            stringpowers.append(stringoutput['p'])
            stringratedpowers.append(stringoutput['rp'])
            stringidealpowers.append(stringoutput['ip'])
        pvStrings.append(string_info)

    if len(stringcurrents) != 0:
        stringcombineroutput = {
            'c': round(np.sum(stringcurrents), 3),
            'v': round(np.mean(stringvoltages), 3), 
            'p': round(np.sum(stringpowers), 3), 
#            'rp': round(np.sum(stringratedpowers), 3), 
#            'ip': round(np.sum(stringidealpowers), 3) 
        }
        stringcombineroutput['u'] = round(stringcombineroutput['p']/60,3) # Divide by to get energy in kWh. 1kWh = 1 unit of energy. 
        
#        stringcombineroutput['eff'] = component_efficiency(stringcombineroutput['p'], stringcombineroutput['ip'])
        # stringcombineroutput['perf'] = component_performance(stringcombineroutput['eff'])

        string_iterator_output['o'] = stringcombineroutput
        string_iterator_output['cuml'] = stringcombinerlosses
        # string_iterator_output['pvStrings'] = pvStrings # Commented to reduce output file size. Check if it is commented above at initializing.

        return string_iterator_output
    
    else:
        return string_iterator_output

# Iterating over the scbs connected to an inverter/inverter unit. 
# Gives the input of a single inverter/inverter-unit containing scbs. 
def stringmodule_iterator(string_module_data, wmsdata, plant_specific_data, scb_rt):

    stringmodulecurrents, stringmodulevoltages, stringmodulepowers, stringmoduleratedpowers, stringmoduleidealpowers = [], [], [], [], []

    scbs_list = []
    aggregated_scb_losses = initiate_losses()
    scb_iterator_output = {
        'deviceid': string_module_data['deviceid'], 
        # 'devicename': string_module_data['devicename'], 
        'isDeleted': string_module_data['isDeleted'], 
        'o': None, 'cuml': None, 'scbs': None
    }

    if 'poa' in wmsdata.keys():
        poa = wmsdata['poa']
    elif 'gti' in wmsdata.keys():
        poa = wmsdata['gti']
    else:
        poa = 0
    scbconfig = {}
    for scbindex, scb in enumerate(scb_rt['scbs']):
        scbconfig[scb["deviceid"]] = scb
    
    for stringmoduleindex, stringmodule in enumerate(string_module_data['scbs']):
        if stringmodule['deviceid'] in scbconfig:
            rt_data_sub = scbconfig[stringmodule['deviceid']]
            dccap = stringmodule['dccapacity']

            if (stringmodule['isDeleted'] is False) and (len(stringmodule['pvStrings']) > 0):
            # if 'pvStrings' in stringmodule.keys():
                string_iterator_output = string_iterator(stringmodule, wmsdata, plant_specific_data, rt_data_sub)
                if string_iterator_output['o'] is not None:
                    # string_iterator_output['o']['locl'] = string_iterator_output['cuml']
                    stringmoduleoutput, stringmodulelosses = string_iterator_output['o'], string_iterator_output['cuml']

                    aggregated_scb_losses = compile_losses(aggregated_scb_losses, stringmodulelosses)

                    if 'pwr' in rt_data_sub.keys() and (string_iterator_output['o'] is not None) and rt_data_sub['pwr'] != 0:
                        string_iterator_output['o']['d'] = round((string_iterator_output['o']['p'] - rt_data_sub['pwr'])/rt_data_sub['pwr'], 3)
                        # string_iterator_output['o']['perf'] = component_performance(rt_data_sub['pwr']/string_iterator_output['o']['p']*1000)
                        string_iterator_output['o']['perf'] = component_performance(rt_data_sub['pwr']/(dccap*poa/1000)*1000) if (poa != 0 and dccap != 0) else component_performance(-1)
                    elif string_iterator_output['o'] is not None:
                        string_iterator_output['o']['d'] = 9999 
                        string_iterator_output['o']['perf'] = component_performance(-1)
                    else:
                        pass

                    if stringmoduleoutput is not None:
                        stringmodulecurrents.append(stringmoduleoutput['c'])
                        stringmodulevoltages.append(stringmoduleoutput['v'])
                        stringmodulepowers.append(stringmoduleoutput['p'])
                        #stringmoduleratedpowers.append(stringmoduleoutput['rp'])
                        #stringmoduleidealpowers.append(stringmoduleoutput['ip'])

                    scbs_list.append(string_iterator_output)
                else:
                    print(f"None output returned from string iter in scb iter.")

    if len(stringmodulecurrents) != 0:
        aggregated_scb_output = {
            'c': round(np.sum(stringmodulecurrents), 3),
            'v': round(np.mean(stringmodulevoltages), 3), 
            'p': round(np.sum(stringmodulepowers), 3), 
        #    'rp': round(np.sum(stringmoduleratedpowers), 3), 
        #    'ip': round(np.sum(stringmoduleidealpowers), 3) 
        }
        # aggregated_scb_output['d'] = round((aggregated_scb_output['p'] - scb_rt['pwr'])/scb_rt['pwr'], 3) if scb_rt['pwr'] != 0. else 0
        #aggregated_scb_output['eff'] = component_efficiency(aggregated_scb_output['p'], aggregated_scb_output['ip'])
        # aggregated_scb_output['perf'] = component_performance(aggregated_scb_output['eff'])

        scb_iterator_output['o'] = aggregated_scb_output
        scb_iterator_output['cuml'] = aggregated_scb_losses
        scb_iterator_output['scbs'] = scbs_list

        return scb_iterator_output
    
    else:
        return scb_iterator_output

# Iterating over the inverters connected to a inverter trafo unit.
# Gives the input of a single inverter trafo containing multiple inverters.
def inverter_iterator(inverter_data, wmsdata, plant_specific_data, inv_rt):
    # Commented code changes it to recursive function removing need for different function for inverter units.
    # Note tested hence commented. 
    from modules.inverter import InverterMain

    inverters_list = []
    aggregated_losses = initiate_losses()
    inverter_iterator_output = {
        # 'devicename': inverter_data['devicename'], 
        'deviceid': inverter_data['deviceid'], 
        'isDeleted': inverter_data['isDeleted'], 
        'o': None, 'cuml': None, 'inverters': None
    }

    if 'poa' in wmsdata.keys():
        poa = wmsdata['poa']
    elif 'gti' in wmsdata.keys():
        poa = wmsdata['gti']
    else:
        poa = 0

    invconfig = {}
    for inverterindex, inverter in enumerate(inv_rt['inverters']):
        invconfig[inverter['deviceid']] = inverter

    if 'inverters' in inverter_data.keys():
    # if ('inverters' in inverter_data.keys()) or ('inverterunits' in inverter_data.keys()):
        invcurrents, invvoltages, invpowers, invratedpowers, invefficiency = [], [], [], [], []

        # if 'inverters' in inverter_data.keys():
        #     key_name = 'inverters'
        # else:
        #     key_name = 'inverterunits'
        for inverterindex, inverter in enumerate(inverter_data['inverters']):
        # for inverterindex, inverter in enumerate(inverter_data[key_name]):

            if inverter['deviceid'] in invconfig:
                rt_data_sub = inv_rt['inverters'][inverterindex]
                dccap = inverter['dccapacity']

                if 'inverterunits' in inverter.keys():
                    inverter_output_from_sublevel = {
                        # 'devicename': inverter['devicename'], 
                        'deviceid': inverter['deviceid'], 'isDeleted': inverter['isDeleted'], 
                        'o': None, 'cuml': None, 'inverterunits': None
                    }
                    inverter_level_losses = initiate_losses()

                    invunits_iterator_output = inverterunits_iterator(inverter, wmsdata, plant_specific_data, rt_data_sub)
                    if invunits_iterator_output['o'] is not None:
                        inverter_output, inverter_losses = invunits_iterator_output['o'], invunits_iterator_output['cuml']
                        inverter_output_from_sublevel['o'] = inverter_output
                        inverter_output_from_sublevel['cuml'] = inverter_losses
                        inverter_level_losses = compile_losses(inverter_level_losses, inverter_losses)

                        inverter_output_from_sublevel['inverterunits'] = invunits_iterator_output['inverterunits']

                        inverters_list.append(inverter_output_from_sublevel)

                        # inverter_output_current, inverter_output_voltage = inverter_iterator(inverter, wmsdata, plant_specific_data)

                        invcurrents.append(inverter_output['c']), invvoltages.append(inverter_output['v']), invpowers.append(inverter_output['p'])
                        # invratedpowers.append(inverter_output['rated_power']) 
                        invefficiency.append(inverter_output['eff'])
                    else:
                        print(f"none output from invunits iter in inv iter.")

                elif 'scbs' in inverter.keys() and inverter['isstringinverter'] is False:
                    inverter_output_from_sublevel = {
                        # 'devicename': inverter['devicename'], 
                        'deviceid': inverter['deviceid'], 'isDeleted': inverter['isDeleted'], 
                        'o': None, 'cuml': None, 'scbs': None
                    }

                    inverter_level_losses = initiate_losses()
                    
                    scb_iterator_output = stringmodule_iterator(inverter, wmsdata, plant_specific_data, rt_data_sub)
                    if scb_iterator_output['o'] is not None:
                        inverter_inputs, inverter_input_losses = scb_iterator_output['o'], scb_iterator_output['cuml']
                        inverter_output_from_sublevel['scbs'] = scb_iterator_output['scbs']

                        inverter_input_current = inverter_inputs['c']
                        inverter_input_voltage = inverter_inputs['v']

                        if inverter_input_current is not None:
                            if inverter['isDeleted'] is False:
                                if 'cableConfig' in inverter.keys():
                                    cable_config = inverter['cableConfig']
                                else:
                                    cable_config = None

                                if 'connectorConfig' in inverter.keys():
                                    connector_config = inverter['connectorConfig']
                                else:
                                    connector_config = None

                                inverter_config_ = {}
                                inverter_config_['rated_power'] = inverter['rating']
                                inverter_config_['rated_vlt'] = inverter['ratedVlt'] 

                                inverter_config = {'cable': cable_config, 'connector': connector_config, 'inverter': inverter_config_}

                                inverter_output, inverter_losses = InverterMain(inverter_input_current, inverter_input_voltage, inverter_config, wmsdata['ambTemp'])
                                inverter_output['locl'] = inverter_losses
                                inverter_output_from_sublevel['o'] = inverter_output

                                if 'pwr' in rt_data_sub.keys() and rt_data_sub['pwr'] != 0:
                                    inverter_output_from_sublevel['o']['d'] = round((inverter_output_from_sublevel['o']['p']/1000.  - rt_data_sub['pwr'])/rt_data_sub['pwr'], 3)
                                    # inverter_output_from_sublevel['o']['perf'] = component_performance(rt_data_sub['pwr']/inverter_output_from_sublevel['o']['p']*1000)
                                    inverter_output_from_sublevel['o']['perf'] = component_performance(rt_data_sub['pwr']/(dccap*poa/1000)*1000) if (poa != 0 and dccap != 0) else component_performance(-1)                            
                                else:
                                    inverter_output_from_sublevel['o']['d'] = 9999
                                    inverter_output_from_sublevel['o']['perf'] = component_performance(-1)

                                inverter_level_losses = compile_losses(inverter_level_losses, inverter_losses)
                                inverter_level_losses = compile_losses(inverter_level_losses, inverter_input_losses, efficiency=1.0)
                                inverter_output_from_sublevel['cuml'] = inverter_level_losses

                                invcurrents.append(inverter_output['c'])
                                invvoltages.append(inverter_output['v'])
                                invpowers.append(inverter_output['p']) 
                                # invratedpowers.append(inverter_output['rated_power']) 
                                invefficiency.append(inverter_output['eff'])

                        inverters_list.append(inverter_output_from_sublevel)
                    else:
                        print(f"None output from scb iter in inv iter.")
                # in case of string inverters:
                 
                elif 'isstringinverter' in inverter.keys()  and inverter['isstringinverter'] is True:
                    inverter_output_from_sublevel = {
                        # 'devicename': inverter['devicename'], 
                        'deviceid': inverter['deviceid'], 'isDeleted': inverter['isDeleted'], 
                        'o': None, 'cuml': None, 'pvStrings': None
                    }
                    inverter_level_losses = initiate_losses()
                    
                    inverter_input_current=[]
                    inverter_input_voltage=[]
                    pvstrings=[]
                    for string_ in range(len(inverter['pvStrings'])):                    
                        string_iterator_output = string_iterator(inverter, wmsdata, plant_specific_data, rt_data_sub)

                        if string_iterator_output['o'] is not None:
                            inverter_inputs, inverter_input_losses = string_iterator_output['o'], string_iterator_output['cuml']
                            pvstrings.append(string_iterator_output['o'])
                            

                            inverter_input_current.append(inverter_inputs['c'])
                            inverter_input_voltage.append(inverter_inputs['v'])
                             
                    inverter_output_from_sublevel['pvStrings'] = pvstrings
                    if sum(inverter_input_current) is not None:
                        if inverter['isDeleted'] is False:
                            if 'cableConfig' in inverter.keys():
                                cable_config = inverter['cableConfig']
                            else:
                                cable_config = None

                            if 'connectorConfig' in inverter.keys():
                                connector_config = inverter['connectorConfig']
                            else:
                                connector_config = None

                            inverter_config_ = {}
                            inverter_config_['rated_power'] = inverter['rating']
                            inverter_config_['rated_vlt'] = inverter['ratedVlt'] 

                            inverter_config = {'cable': cable_config, 'connector': connector_config, 'inverter': inverter_config_}

                            inverter_output, inverter_losses = InverterMain(sum(inverter_input_current),np.average(inverter_input_voltage) , inverter_config, wmsdata['ambTemp'])
                            inverter_output['locl'] = inverter_losses
                            inverter_output_from_sublevel['o'] = inverter_output

                            if 'pwr' in rt_data_sub.keys() and rt_data_sub['pwr'] != 0:
                                inverter_output_from_sublevel['o']['d'] = round((inverter_output_from_sublevel['o']['p']/1000.  - rt_data_sub['pwr'])/rt_data_sub['pwr'], 3)
                                # inverter_output_from_sublevel['o']['perf'] = component_performance(rt_data_sub['pwr']/inverter_output_from_sublevel['o']['p']*1000)
                                inverter_output_from_sublevel['o']['perf'] = component_performance(rt_data_sub['pwr']/(dccap*poa/1000)*1000) if (poa != 0 and dccap != 0) else component_performance(-1)                            
                            else:
                                inverter_output_from_sublevel['o']['d'] = 9999
                                inverter_output_from_sublevel['o']['perf'] = component_performance(-1)

                            inverter_level_losses = compile_losses(inverter_level_losses, inverter_losses)
                            inverter_level_losses = compile_losses(inverter_level_losses, inverter_input_losses, efficiency=1.0)
                            inverter_output_from_sublevel['cuml'] = inverter_level_losses

                            invcurrents.append(inverter_output['c'])
                            invvoltages.append(inverter_output['v'])
                            invpowers.append(inverter_output['p']) 
                            # invratedpowers.append(inverter_output['rated_power']) 
                            invefficiency.append(inverter_output['eff'])

                        inverters_list.append(inverter_output_from_sublevel)
                    else:
                        print(f"None output from scb iter in inv iter.")
                    
                    
                aggregated_losses = compile_losses(aggregated_losses, inverter_level_losses)
            else:
                print('inverter device id mismatch.')

        if len(invcurrents) != 0:
            aggregated_output = {
                'c': round(np.sum(invcurrents), 3), 
                'v': round(np.mean(invvoltages), 3), 
                'p': round(np.sum(invpowers), 3), 
                # 'rated_power': np.sum(invratedpowers), 
                'eff': round(np.mean(invefficiency), 3)
            }
            # aggregated_output['d'] = round((aggregated_output['p'] - inv_rt['pwr'])/inv_rt['pwr'], 3) if inv_rt['pwr'] != 0. else 0
            # aggregated_output['perf'] = component_performance(aggregated_output['eff'])

            inverter_iterator_output['o'] = aggregated_output
            inverter_iterator_output['cuml'] = aggregated_losses
            inverter_iterator_output['inverters'] = inverters_list

            return inverter_iterator_output
        else:
            return inverter_iterator_output


# Iterating over the inverter units connected to an inverter.
# Gives the input of a single inverter (containing inverter units only).
def inverterunits_iterator(inverterunit_data, wmsdata, plant_specific_data, invunit_rt):
    from modules.inverter import InverterMain

    invunits_list = []
    aggregated_losses = initiate_losses()
    invunits_iterator_output = {
        'deviceid': inverterunit_data['deviceid'], 
        # 'devicename': inverterunit_data['devicename'], 
        'isDeleted': inverterunit_data['isDeleted'], 
        'o': None, 'cuml': None, 'inverterunits': None
    }

    if 'poa' in wmsdata.keys():
        poa = wmsdata['poa']
    elif 'gti' in wmsdata.keys():
        poa = wmsdata['gti']
    else:
        poa = 0

    invunitconfig = {}
    for inverterindex, inverter in enumerate(inverterunit_data['inverterunits']):
        invunitconfig[inverter['deviceid']] = inverter

    if 'inverterunits' in inverterunit_data.keys(): #this condition can be removed if inverterunits is checked before. 
        invcurrents, invvoltages, invpowers, invratedpowers, invefficiency = [], [], [], [], []

        for inverterindex, inverter in enumerate(inverterunit_data['inverterunits']):

            if inverter['deviceid'] in invunitconfig:
                rt_data_sub = inverterunit_data['inverterunits'][inverterindex]
                dccap = inverter['dccapacity']

                invunit_output = {}
                # invunit_output['devicename'] = inverter['devicename']
                invunit_output['deviceid'] = inverter['deviceid']
                invunit_output['isDeleted'] = inverter['isDeleted']
                invunit_output['o'], invunit_output['cuml'], invunit_output['scbs'] = None, None, None

                invunit_level_losses = initiate_losses()

                inverter_inputs = stringmodule_iterator(inverter, wmsdata, plant_specific_data, rt_data_sub)
                invunit_output['scbs'] = inverter_inputs['scbs']

                if inverter_inputs['o'] is not None:
                    inverter_input_losses = inverter_inputs['cuml']
                    inverter_input_current = inverter_inputs['o']['c']
                    inverter_input_voltage = inverter_inputs['o']['v']

                    if inverter_input_current is not None:
                        if inverter['isDeleted'] is False:
                            if 'cableConfig' in inverter.keys():
                                cable_config = inverter['cableConfig']
                            else:
                                cable_config = None

                            if 'connectorConfig' in inverter.keys():
                                connector_config = inverter['connectorConfig']
                            else:
                                connector_config = None

                            inverter_config_ = {}
                            inverter_config_['rated_power'] = inverter['rating']
                            inverter_config_['rated_vlt'] = inverter['ratedVlt'] 

                            inverter_config = {'cable': cable_config, 'connector': connector_config, 'inverter': inverter_config_}

                            inverter_output, inverter_losses = InverterMain(inverter_input_current, inverter_input_voltage, inverter_config, wmsdata['ambTemp'])
                            inverter_output['locl'] = inverter_losses
                            invunit_output['o'] = inverter_output

                            if 'pwr' in rt_data_sub.keys() and rt_data_sub['pwr'] != 0:
                                invunit_output['o']['d'] = round((invunit_output['o']['p']/1000.  - rt_data_sub['pwr'])/rt_data_sub['pwr'], 3)
                                # invunit_output['o']['perf'] = component_performance(rt_data_sub['pwr']/invunit_output['o']['p']*1000)
                                invunit_output['o']['perf'] = component_performance(rt_data_sub['pwr']/(dccap*poa/1000)*1000) if (poa != 0 and dccap != 0) else component_performance(-1)
                            else:
                                invunit_output['o']['d'] = 9999
                                invunit_output['o']['perf'] = component_performance(-1)

                            invunit_level_losses = compile_losses(invunit_level_losses, inverter_losses)
                            invunit_level_losses = compile_losses(invunit_level_losses, inverter_input_losses, efficiency=1.0)
                            invunit_output['cuml'] = invunit_level_losses

                            invcurrents.append(inverter_output['c'])
                            invvoltages.append(inverter_output['v'])
                            invpowers.append(inverter_output['p'])
                            # invratedpowers.append(inverter_output['rated_power'])
                            invefficiency.append(inverter_output['eff'])

                            # invohmicloss.append(inverter_losses['ohmicloss'] + inverter_input_losses['ohmicloss']*inverter_output['efficiency'])
                            # invtemploss.append(inverter_losses['temperatureloss'] + inverter_input_losses['temperatureloss']*inverter_output['efficiency'])
                            # invjointloss.append(inverter_input_losses['jointloss']*inverter_output['efficiency'])
                            # inviamloss.append(inverter_input_losses['iamloss']*inverter_output['efficiency'])
                            # invoversizingloss.append(inverter_losses['oversizingloss'])

                            # print(f"\n{pqmindex}, {ogtrafoindex}, {icrindex}, {ictindex}, {inverterindex}")
                            # print(invcurrents)
                    invunits_list.append(invunit_output)
                    aggregated_losses = compile_losses(aggregated_losses, invunit_level_losses)
                else:
                    print(f"none output from scb iter output in invunits iter.")
            else:
                print('Inverter units device id mismatch.')
        

        if len(invcurrents) != 0:
            aggregated_output = {
                'c': round(np.sum(invcurrents), 3), 
                'v': round(np.mean(invvoltages), 3), 
                'p': round(np.sum(invpowers), 3), 
                # 'rated_power': np.sum(invratedpowers), 
                'eff': round(np.mean(invefficiency), 3)
            }
            # aggregated_output['d'] = round((aggregated_output['p'] - invunit_rt['pwr'])/invunit_rt['pwr'], 3) if invunit_rt['pwr'] != 0. else 0
            # aggregated_output['perf'] = component_performance(aggregated_output['eff'])

            invunits_iterator_output['o'] = aggregated_output
            invunits_iterator_output['cuml'] = aggregated_losses
            invunits_iterator_output['inverterunits'] = invunits_list

            return invunits_iterator_output
        else:
            return invunits_iterator_output

# Iterating over transformers (inv trafo or power trafo) connected to either blocks or other transformers.
# Gives the input to the block or transformer.
def trafo_iterator(trafo_data, wmsdata, plant_specific_data, trafo_rt):
    from modules.transformer import TransformerMain

    if 'poa' in wmsdata.keys():
        poa = wmsdata['poa']
    elif 'gti' in wmsdata.keys():
        poa = wmsdata['gti']
    else:
        poa = 0

    trafoconfig = {}
    for trafoindex, trafo in enumerate(trafo_rt['trafos']):
        trafoconfig[trafo['deviceid']] = trafo

    if 'trafos' in trafo_data.keys():
        trafocurrents, trafovoltages, trafopowers, traforatedpowers, trafoeff = [], [], [], [], []

        aggregated_losses = initiate_losses()
        if 'deviceid' in trafo_data.keys():
            trafo_iterator_output_final = {
                # 'devicename': trafo_data['devicename'],
                'deviceid': trafo_data['deviceid'],  
                'o': None, 'cuml': None, 'trafos': None
            }
            if 'isDeleted' in trafo_data.keys():
                trafo_iterator_output_final['isDeleted'] = trafo_data['isDeleted']
                
        elif 'blockid' in trafo_data.keys():
            trafo_iterator_output_final = {
                # 'blockname': trafo_data['blockname'], 
                'blockid': trafo_data['blockid'], 'isDeleted': trafo_data['isDeleted'], 
                'o': None, 'cuml': None, 'trafos': None
            }
        else:
            trafo_iterator_output_final = {
                'o': None, 'cuml': None, 'trafos': None
            }
        sublevel_list = []

        for trafoindex, trafo in enumerate(trafo_data['trafos']):
            if trafo['deviceid'] in trafoconfig:
                trafo_level_losses = initiate_losses()

                rt_data_sub = trafo_rt['trafos'][trafoindex]
                dccap = trafo['dccapacity']

                if 'inverters' in trafo.keys():
                    trafo_output_from_sublevel = {
                        # 'devicename': trafo['devicename'], 
                        'deviceid': trafo['deviceid'], 'isDeleted': trafo['isDeleted'], 
                        'o': None, 'cuml': None, 'inverters': None
                    }
                    inverter_iterator_output = inverter_iterator(trafo, wmsdata, plant_specific_data, rt_data_sub)
                    output, losses = inverter_iterator_output['o'], inverter_iterator_output['cuml']
                    trafo_output_from_sublevel['inverters'] = inverter_iterator_output['inverters']

                    trafo_input_current, trafo_input_voltage = output['c'], output['v']
                    trafo_level_losses = compile_losses(trafo_level_losses, losses)
                elif 'trafos' in trafo.keys():
                    trafo_output_from_sublevel = {
                        # 'devicename': trafo['devicename'], 
                        'deviceid': trafo['deviceid'], 'isDeleted': trafo['isDeleted'], 
                        'o': None, 'cuml': None, 'trafos': None
                    }
                    trafo_iterator_output = trafo_iterator(trafo, wmsdata, plant_specific_data, rt_data_sub)
                    output, losses = trafo_iterator_output['o'], trafo_iterator_output['cuml']
                    trafo_output_from_sublevel['trafos'] = trafo_iterator_output['trafos']

                    trafo_input_current, trafo_input_voltage = output['c'], output['v']
                    trafo_level_losses = compile_losses(trafo_level_losses, losses)
                elif 'icrs' in trafo.keys():
                    trafo_output_from_sublevel = {
                        # 'devicename': trafo['devicename'], 
                        'deviceid': trafo['deviceid'], 'isDeleted': trafo['isDeleted'], 
                        'o': None, 'cuml': None, 'icrs': None
                    }
                    icrs_iterator_output = icrs_iterator(trafo, wmsdata, plant_specific_data, rt_data_sub)
                    output, losses = icrs_iterator_output['o'], icrs_iterator_output['cuml']
                    trafo_output_from_sublevel['icrs'] = icrs_iterator_output['icrs']

                    trafo_input_current, trafo_input_voltage = output['c'], output['v']
                    trafo_level_losses = compile_losses(trafo_level_losses, losses)
                else:
                    trafo_input_current, trafo_input_voltage = 0, 1
                    trafo_output_from_sublevel = None
                    output, losses = None, None
                    warnings.warn('Transformer connected to unknown component. Trafo inputs assumed 0.')

                if output is not None:
                    if trafo['isDeleted'] is False:
                        if 'cableConfig' in trafo.keys():
                            cable_config = trafo['cableConfig']
                        else:
                            cable_config = None

                        if 'connectorConfig' in trafo.keys():
                            connector_config = trafo['connectorConfig']
                        else:
                            connector_config = None

                        trafo_config = {}
                        trafo_config['rated_power'] = trafo['kvaRating']
                        trafo_config['thermal_coeff'] = trafo['tempEffect']
                        trafo_config['winding_ratio'] = trafo['lowRatio'] / trafo['highRatio']
                        trafo_config['fixedLosses'] = trafo['fixedLosses']
                        trafo_config['lvResistance'] = trafo['lvResistance']
                        trafo_config['hvResistance'] = trafo['hvResistance']

                        transformer_config = {'cable': cable_config, 'connector': connector_config, 'trafo': trafo_config}

                        trafo_output, trafo_losses = TransformerMain(trafo_input_current, trafo_input_voltage, transformer_config, wmsdata['ambTemp'])
                        trafo_output['locl'] = trafo_losses
                        trafo_output_from_sublevel['o'] = trafo_output

                        if 'pwr' in rt_data_sub.keys() and rt_data_sub['pwr'] != 0:
                            trafo_output_from_sublevel['o']['d'] = round((trafo_output_from_sublevel['o']['p']/1000.  - rt_data_sub['pwr'])/rt_data_sub['pwr'], 3)
                            # trafo_output_from_sublevel['o']['perf'] = component_performance(rt_data_sub['pwr']/trafo_output_from_sublevel['o']['p']*1000)
                            trafo_output_from_sublevel['o']['perf'] = component_performance(rt_data_sub['pwr']/(dccap*poa/1000)*1000) if (poa != 0 and dccap != 0) else component_performance(-1)
                        else:
                            trafo_output_from_sublevel['o']['d'] = 9999
                            trafo_output_from_sublevel['o']['perf'] = component_performance(-1)

                        trafocurrents.append(trafo_output['c']), trafovoltages.append(trafo_output['v']), trafopowers.append(trafo_output['p'])
                        # traforatedpowers.append(trafo_output['rated_power']) 
                        trafoeff.append(trafo_output['eff'])

                        trafo_level_losses = compile_losses(trafo_level_losses, trafo_losses)

                        trafo_output_from_sublevel['cuml'] = trafo_level_losses

                    sublevel_list.append(trafo_output_from_sublevel)

                    aggregated_losses = compile_losses(aggregated_losses, trafo_level_losses)
                else:
                    print("None output from sublevel of trafo.")
            else:
                print(f"trafo device id mismatch.")

        if len(trafocurrents) != 0:
            aggregated_output = {
                'c': round(np.sum(trafocurrents), 6) if round(np.sum(trafocurrents), 3)==0.000 else round(np.sum(trafocurrents), 3), 
                'v': round(np.mean(trafovoltages), 3),
                'p': round(np.sum(trafopowers), 3), 
                # 'rated_power': np.sum(traforatedpowers), 
                'eff': round(np.mean(trafoeff), 3)
            }
            # aggregated_output['d'] = round((aggregated_output['p'] - trafo_rt['pwr'])/trafo_rt['pwr'], 3) if trafo_rt['pwr'] != 0. else 0
            # aggregated_output['perf'] = component_performance(aggregated_output['eff'])

            trafo_iterator_output_final['o'] = aggregated_output
            trafo_iterator_output_final['cuml'] = aggregated_losses
            trafo_iterator_output_final['trafos'] = sublevel_list

            return trafo_iterator_output_final
        
        else:
            return trafo_iterator_output_final

# Iterating over the icrs or blocks connected to a power tranformer (usually).
# Gives the input to a power transformer or the outputs from a bunch of blocks/icrs. Each icrs contains inverter transformer(s). 
def icrs_iterator(icrs_data, wmsdata, plant_specific_data, icrs_rt):

    icrs_list = []
    aggregated_losses = initiate_losses()
    icrs_iterator_output = {
        # 'devicename': icrs_data['devicename'], 
        'deviceid': icrs_data['deviceid'], 
        'isDeleted': icrs_data['isDeleted'], 
        'o': None, 'cuml': None, 'icrs': None
    }

    if 'poa' in wmsdata.keys():
        poa = wmsdata['poa']
    elif 'gti' in wmsdata.keys():
        poa = wmsdata['gti']
    else:
        poa = 0

    icrsconfig = {}
    for icrindex, icr in enumerate(icrs_rt['icrs']):
        icrsconfig[icr['blockid']] = icr
        
    if 'icrs' in icrs_data.keys():
        icrcurrents, icrvoltages, icrpowers, icr_ratedpowers, icr_eff = [], [], [], [], []

        for icrindex, icr in enumerate(icrs_data['icrs']):
            if icr['blockid'] in icrsconfig:
                rt_data_sub = icrs_rt['icrs'][icrindex]
                dccap = icr['dccapacity']

                icrtrafo_iterator_output = trafo_iterator(icr, wmsdata, plant_specific_data, rt_data_sub)
                # icrtrafo_iterator_output['output']['losses'] = icrtrafo_iterator_output['losses']
                output, losses = icrtrafo_iterator_output['o'], icrtrafo_iterator_output['cuml']

                if output is not None:
                    if 'pwr' in rt_data_sub.keys() and rt_data_sub['pwr'] != 0:
                        icrtrafo_iterator_output['o']['d'] = round((icrtrafo_iterator_output['o']['p']/1000.  - rt_data_sub['pwr'])/rt_data_sub['pwr'], 3)
                        # icrtrafo_iterator_output['o']['perf'] = component_performance(rt_data_sub['pwr']/icrtrafo_iterator_output['o']['p']*1000)
                        icrtrafo_iterator_output['o']['perf'] = component_performance(rt_data_sub['pwr']/(dccap*poa/1000)*1000) if (poa != 0 and dccap != 0) else component_performance(-1)
                    else:
                        icrtrafo_iterator_output['o']['d'] = 9999
                        icrtrafo_iterator_output['o']['perf'] = component_performance(-1)

                    icrs_list.append(icrtrafo_iterator_output)

                    aggregated_losses = compile_losses(aggregated_losses, losses)

                    icrcurrents.append(output['c']), icrvoltages.append(output['v']), icrpowers.append(output['p'])
                    # icr_ratedpowers.append(output['rated_power']) 
                    icr_eff.append(output['eff'])
                else:
                    print(f"None output from inverter trafo.")
            else:
                print('icrs block id mismatch.')

        if len(icrcurrents) != 0:
            aggregated_output = {
                'c': round(np.sum(icrcurrents),6) if round(np.sum(icrcurrents),3) == 0.000 else round(np.sum(icrcurrents),3), 
                'v': round(np.mean(icrvoltages), 3),
                'p': round(np.sum(icrpowers), 3), 
                # 'rated_power': np.sum(icr_ratedpowers), 
                'eff': round(np.mean(icr_eff), 3)                
            }
            # aggregated_output['d'] = round((aggregated_output['p'] - icrs_rt['pwr'])/icrs_rt['pwr'], 3) if icrs_rt['pwr'] != 0. else 0
            # aggregated_output['perf'] = component_performance(aggregated_output['eff'])

            icrs_iterator_output['o'] = aggregated_output
            icrs_iterator_output['cuml'] = aggregated_losses
            icrs_iterator_output['icrs'] = icrs_list

            return icrs_iterator_output
        else:
            return icrs_iterator_output

# Iterating over the final outgoing trafos before the poi or other points of measurement.
# Gives the plant output.
def pqm_iterator(plant_data, wmsdata, plant_specific_data, rt_data):

    aggregated_losses = initiate_losses()
    sub_units_list = []
    pqm_iterator_output = {
        'o': None, 'cuml': None
    }

    if 'poa' in wmsdata.keys():
        poa = wmsdata['poa']
    elif 'gti' in wmsdata.keys():
        poa = wmsdata['gti']
    else:
        poa = 0
    poaconfig = {}
    for pqmindex, pqm in enumerate(rt_data['trafos']):
        poaconfig[pqm['deviceid']] = pqm

    if 'trafos' in plant_data.keys():
        pqm_iterator_output['trafos'] = None

        pqmcurrents, pqmvoltages, pqmpowers, pqm_ratedpowers, pqm_eff = [], [], [], [], []

        for pqmindex, pqm in enumerate(plant_data['trafos']):
            if pqm['deviceid'] in poaconfig:
                pqm_rt = rt_data['trafos'][pqmindex]
                dccap = pqm['dccapacity']

                trafo_iterator_output = trafo_iterator(pqm, wmsdata, plant_specific_data, pqm_rt)
                # trafo_iterator_output['output']['losses'] = trafo_iterator_output['losses']
                output, losses = trafo_iterator_output['o'], trafo_iterator_output['cuml']

                if output is not None:
                    if 'pwr' in pqm_rt.keys() and pqm_rt['pwr'] != 0:
                        trafo_iterator_output['o']['d'] = round((trafo_iterator_output['o']['p']/1_000 - pqm_rt['pwr'])/pqm_rt['pwr'], 3)
                        # trafo_iterator_output['o']['perf'] = component_performance(pqm_rt['pwr']/trafo_iterator_output['o']['p']*1_000)
                        trafo_iterator_output['o']['perf'] = component_performance(pqm_rt['pwr']/(dccap*poa/1000)*1_000) if (poa != 0 and dccap != 0) else component_performance(-1)
                    else:
                        trafo_iterator_output['o']['d'] = 9999
                        trafo_iterator_output['o']['perf'] = component_performance(-1)

                    sub_units_list.append(trafo_iterator_output)

                    aggregated_losses = compile_losses(aggregated_losses, losses)

                    pqmcurrents.append(output['c']), pqmvoltages.append(output['v']), pqmpowers.append(output['p'])
                    # pqm_ratedpowers.append(output['rated_power']) 
                    pqm_eff.append(output['eff'])
                else:
                    print(f"None output from trafo at poi.")
            else:
                print('poa device id mismatch.')
                
        aggregated_output = {
            'c': round(np.sum(pqmcurrents), 6) if round(np.sum(pqmcurrents), 3) == 0.000 else round(np.sum(pqmcurrents), 3), 
            'v': round(np.mean(pqmvoltages), 3), 
            'p': round(np.sum(pqmpowers), 3), 
            # 'rated_power': np.sum(pqm_ratedpowers), 
            'eff': round(np.mean(pqm_eff), 3)
        }

        # aggregated_output['perf'] = component_performance(aggregated_output['eff'])
        
        pqm_iterator_output['o'] = aggregated_output
        pqm_iterator_output['cuml'] = aggregated_losses
        pqm_iterator_output['trafos'] = sub_units_list

        return pqm_iterator_output

