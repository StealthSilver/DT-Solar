from math import sin, cos, radians, degrees, acos

def IncidanceAngleLosses(
    startdate, latitude, tiltangle, reftime, Azimuthalangle, irradiation
):
    solarday = (reftime.date() - startdate).days + 1
    # HourAngle calculation:
    to = reftime.hour + (reftime.minute / 60)
    HourAngle = 15 * (to - 12)  # degrees
    # delta angle calculations:
    Deltaangle = (23.45 * (sin(radians((360 / 365) * (solarday - 81)))))
    # altitude angle:
    # AltitudeAnglerad = cos(radians(latitude)) * cos(radians(Deltaangle)) * cos(
    #    radians(HourAngle)
    # ) + (sin(radians(latitude)) * sin(radians(Deltaangle)))
    
    # AltitudeAngle = degrees(asin(radians(degrees(AltitudeAnglerad))))
    # Incidence angle:
    incidancerad = (
          (
            sin(radians(latitude)) 
            * sin(radians(Deltaangle) 
            * cos(radians(tiltangle)))
            )
        - (
            cos(radians(latitude))
            * sin(radians(Deltaangle))
            * sin(radians(tiltangle))
            * cos(radians(Azimuthalangle))
             )   
        + (
            cos(radians(latitude))
            * cos(radians(Deltaangle))
            * cos(radians(HourAngle)) 
            * cos(radians(tiltangle))
            )
                     
        + (
            cos(radians(HourAngle))
            * sin(radians(tiltangle))
            * cos(radians(Azimuthalangle))
            * cos(radians(Deltaangle))
            * sin(radians(latitude))
            )
        + (
            cos(radians(Deltaangle))
            * sin(radians(HourAngle))
            * sin(radians(tiltangle))
            * sin(radians(Azimuthalangle))
            )
                )
    IncidanceAngle = degrees(acos(incidancerad))
    fiam = (1 - 0.05 * ((1 / abs(incidancerad)) - 1))
    fiam = fiam if abs(incidancerad) >= 0.05 else 0

    corrected_irradiation = fiam * irradiation

    return fiam, corrected_irradiation