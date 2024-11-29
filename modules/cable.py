import math
#from config import DECIMAL_POINT

def CableDrop(CableConfig, Temperature, Current):
    CableLength, Resistancepermeter, ThermalCoeff = (CableConfig['length'], CableConfig['resPerMeter'], CableConfig['tempCoeff'])
    cableresistance = CableLength*Resistancepermeter*(1+ThermalCoeff*(Temperature-25))
    cabledrop = Current*cableresistance
    return 0 if math.isnan(cabledrop) else cabledrop


def OhmicLoss(CableConfig, temperature, current):
    cablelength, resistancepermeter, thermalcoeff = (CableConfig['length'], CableConfig['resPerMeter'], CableConfig['tempCoeff'])
    ohmicLoss = current**2*cablelength*resistancepermeter * (1+thermalcoeff*(temperature-25))
    return 0 if math.isnan(ohmicLoss) else ohmicLoss