import math
#from config import DECIMAL_POINT

def JointLoss(ConnectorConfig, current, temperature):
    connectorresistance, connectortempcoeff = ConnectorConfig['connector_resistance'], ConnectorConfig['thermal_coeff']
    jointLoss = current**2 * connectorresistance * (1 + connectortempcoeff * (temperature - 25))
    return 0 if math.isnan(jointLoss) else jointLoss

def ConnectorDrop(ConnectorConfig, current, temperature):
    connectorresistance, connectortempcoeff = ConnectorConfig['res'], ConnectorConfig['tempCoeff']
    connectorDrop = (
        current * connectorresistance
        * (1 + (((connectortempcoeff)) * (temperature - 25)))
    )
 #   return 0 if math.isnan(connectorDrop) else round(connectorDrop, DECIMAL_POINT)
    return 0 if math.isnan(connectorDrop) else connectorDrop
