import datetime
from datetime import date
from modules.component_iterators import pqm_iterator
import numpy as np

def DigitalTwinProcess(jsondata):

    plant, wmsdata, timestampRef, rt_data = (
        jsondata["plant"],
        jsondata["wmsdata"],
        jsondata["timestamp"],
        jsondata['rtdata']
    )

    plant_specific_data = {}
    plant_specific_data['latitude'] = plant["latitude"]
    plant_specific_data['tiltangle'] = plant['tiltangle']
    plant_specific_data["azimuthangle"] = plant["azimuthangle"]

    # Calculations start here.
    # output, losses = pqm_iterator(plant, wmsdata, plant_specific_data)
    pqm_iterator_output = pqm_iterator(plant, wmsdata, plant_specific_data, rt_data)

    # return output, losses
    return pqm_iterator_output