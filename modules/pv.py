def PVModule(Vmp, Imp, KVoc, KIsc, ModuleTemperature, correctedirradiation, fiam):
    # The module estimates the pv module output along
    # with temperature and iam losses at module level.
    # input: real values, output: real values in Watts(both electrical output and losses)
    # inputargs = [Vmp, Imp, KVoc, KIsc, ModuleTemperature]
    if Vmp == 0 or Imp == 0 or KVoc == 0 or KIsc == 0:
        raise Exception("Missing PV module mandatory parameters")
    
    modulevoltage, modulecurrent = (
        Vmp * (1 + (KVoc / 100) * (ModuleTemperature - 25)),
        Imp * (1 + (KIsc / 100) * (ModuleTemperature - 25)) * correctedirradiation / 1000,
    )

    module_power, module_ideal_power = modulecurrent * modulevoltage, Vmp * Imp

    module_temperatureloss = module_power - module_ideal_power * correctedirradiation / 1000

    module_iamloss = (1 - fiam) * module_power

    return modulecurrent, modulevoltage, module_temperatureloss, module_iamloss