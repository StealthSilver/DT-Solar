def module_temperature(ambient_temperature, wind_speed, irradiance): 

    from numpy import exp 
   
    # Parameters
    coeff_a, coeff_b, delta_t = -3.47, -0.0594, 3.

    module_back_temp = irradiance * exp(coeff_a + coeff_b * wind_speed) + ambient_temperature

    module_temp = module_back_temp + delta_t * irradiance / 1000

    return module_temp
