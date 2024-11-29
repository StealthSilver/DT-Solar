import datetime
from datetime import date
from modules.string import StringMain
from modules.inverter import InverterMain
from modules.transformer import TransformerMain
import numpy as np

def DigitalTwinProcess(jsondata):

    plant, wmsdata, timestampRef = (
        jsondata["plant"],
        jsondata["wmsdata"],
        jsondata["timestamp"],
    )

    startdate = date(timestampRef.year, 1, 1)
    timestamp = timestampRef 
    # print(timestamp, timestampRef)

    plant_specific_data = {}
    plant_specific_data['latitude'] = plant["latitude"]
    plant_specific_data['tiltangle'] = plant['tiltangle']
    plant_specific_data["azimuthangle"] = plant["azimuthangle"]

    pqms = plant["trafos"]
    irradiation, ambienttemperature = wmsdata["poa"], wmsdata["temperature"]

    pqmcurrents, pqmvoltages = [], []
    for pqmindex, pqm in enumerate(pqms):
        ogtrafocurrents, ogtrafovoltages = [], []
        for ogtrafoindex, ogtrafo in enumerate(pqm['trafos']):
            icrcurrents, icrvoltages = [], []
            for icrindex, icr in enumerate(ogtrafo['icrs']):
                ictcurrents, ictvoltages = [], []
                for ictindex, ict in enumerate(icr['trafos']):
                    invcurrents, invvoltages = [], []
                    for inverterindex, inverter in enumerate(ict['inverters']):
                        stringmodulecurrents, stringmodulevoltages = [], []
                        for stringmoduleindex, stringmodule in enumerate(inverter['scbs']):
                            if stringmodule['isDeleted'] is False:
                                if 'pvStrings' in stringmodule.keys():
                                    stringcurrents, stringvoltages = [], []
                                    for stringindex, string in enumerate(stringmodule['pvStrings']):
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
                                            
                                            string_module_config.append(module_config)

                                            string_config = {}
                                            string_config['cable'] = cable_config
                                            string_config['connector'] = connector_config
                                            string_config['modules'] = string_module_config

                                            #string_current, string_voltage = StringMain(string_config, wmsdata, plant_specific_data)
                                            stringoutput, stringlosses = StringMain(string_config, wmsdata, plant_specific_data)
                                            stringcurrents.append(stringoutput['c'])
                                            stringvoltages.append(stringoutput['v'])                                            
                                    if len(stringcurrents) != 0:
                                        # print(f"\n{pqmindex}, {ogtrafoindex}, {icrindex}, {ictindex}, {inverterindex}, {stringmoduleindex}, {stringindex}")
                                        stringmodulecurrents.append(np.sum(stringcurrents))
                                        stringmodulevoltages.append(np.mean(stringvoltages))

                        #print(f"\n{pqmindex}, {ogtrafoindex}, {icrindex}, {ictindex}, {inverterindex}, {stringmoduleindex}")
                        #print(len(stringmodulecurrents))

                        inverter_input_current, inverter_input_voltage = np.sum(stringmodulecurrents), np.mean(stringmodulevoltages)

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

                            #inverter_output_current, inverter_output_voltage = InverterMain(inverter_input_current, inverter_input_voltage, inverter_config, ambienttemperature)
                            inv_output, inv_losses = InverterMain(inverter_input_current, inverter_input_voltage, inverter_config, ambienttemperature)
                            invcurrents.append(inv_output['c'])
                            invvoltages.append(inv_output['v'])

                            # print(f"\n{pqmindex}, {ogtrafoindex}, {icrindex}, {ictindex}, {inverterindex}")
                            # print(invcurrents)

                    # print(f"\n{pqmindex}, {ogtrafoindex}, {icrindex}, {ictindex}")
                    # print(invcurrents, invvoltages)
                
                    ict_input_current, ict_input_voltage = np.sum(invcurrents), np.mean(invvoltages)

                    if ict['isDeleted'] is False:
                        if 'cableConfig' in ict.keys():
                            cable_config = ict['cableConfig']
                        else:
                            cable_config = None

                        if 'connectorConfig' in ict.keys():
                            connector_config = ict['connectorConfig']
                        else:
                            connector_config = None

                        trafo_config = {}
                        trafo_config['rated_power'] = ict['kvaRating']
                        trafo_config['thermal_coeff'] = ict['tempEffect']
                        trafo_config['winding_ratio'] = ict['lowRatio'] / ict['highRatio']
                        trafo_config['fixedLosses'] = ict['fixedLosses']
                        trafo_config['lvResistance'] = ict['lvResistance']
                        trafo_config['hvResistance'] = ict['hvResistance']

                        transformer_config = {'cable': cable_config, 'connector': connector_config, 'trafo': trafo_config}

                        #ict_output_current, ict_output_voltage = TransformerMain(ict_input_current, ict_input_voltage, transformer_config, ambienttemperature)
                        trafo_output, trafo_losses = TransformerMain(ict_input_current, ict_input_voltage, transformer_config, ambienttemperature)
                        ictcurrents.append(trafo_output['c'])
                        ictvoltages.append(trafo_output['v'])                        
                # print(f"\n{pqmindex}, {ogtrafoindex}, {icrindex}")
                # print(ictcurrents, ictvoltages)

                icrcurrents.append(np.sum(ictcurrents))
                icrvoltages.append(np.mean(ictvoltages))
            # print(f"\n{pqmindex}, {ogtrafoindex}")
            # print(icrcurrents, icrvoltages)

            ogtrafo_input_current, ogtrafo_input_voltage = np.sum(icrcurrents), np.mean(icrvoltages)

            if ogtrafo['isDeleted'] is False:
                if 'cableConfig' in ogtrafo.keys():
                    cable_config = ogtrafo['cableConfig']
                else:
                    cable_config = None
                if 'connectorConfig' in ogtrafo.keys():
                    connector_config = ogtrafo['connectorConfig']
                else:
                    connector_config = None
                
                trafo_config = {}
                trafo_config['rated_power'] = ogtrafo['kvaRating']
                trafo_config['thermal_coeff'] = ogtrafo['tempEffect']
                trafo_config['winding_ratio'] = ogtrafo['lowRatio'] / ogtrafo['highRatio']
                trafo_config['fixedLosses'] = ogtrafo['fixedLosses']
                trafo_config['lvResistance'] = ogtrafo['lvResistance']
                trafo_config['hvResistance'] = ogtrafo['hvResistance']

                transformer_config = {'cable': cable_config, 'connector': connector_config, 'trafo': trafo_config}

                #ogtrafo_output_current, ogtrafo_output_voltage = TransformerMain(ogtrafo_input_current, ogtrafo_input_voltage, transformer_config, ambienttemperature)
                trafo_output, trafo_losses = TransformerMain(ogtrafo_input_current, ogtrafo_input_voltage, transformer_config, ambienttemperature)
                ogtrafocurrents.append(trafo_output['c'])
                ogtrafovoltages.append(trafo_output['v'])                
        # print(f"\n{pqmindex}")
        # print(ogtrafocurrents, ogtrafovoltages)

        pqmcurrents.append(np.sum(ogtrafocurrents))
        pqmvoltages.append(np.mean(ogtrafovoltages))
    
    net_current, net_voltage = np.sum(pqmcurrents), np.mean(pqmvoltages)

    return net_current*net_voltage*1.732
