def component_efficiency(numerator, denominator):
    return round(numerator/denominator, 3)

def component_performance(eff_factor):
    # if eff_factor < 0 or eff_factor > 1:
    #     return -1
    
    if eff_factor >= 0.95 and eff_factor < 10:
        return 0 # Good performance
    elif eff_factor >= 0.90:
        return 1 # Average performance
    elif eff_factor < 0.90 and eff_factor >= 0:
        return 2 # Faulty or poor performance
    else:
        return 9 # Usually real-time data unavailable