def initiate_losses():
    losses = {
        'ol': 0,    # ohmic/cable loss 
        'tl': 0,    # temperature loss
        'jl': 0,    # joint loss
        'il': 0,    # iam loss
        'fl': 0,    # fixed loss in transformer
        'tcl': 0,   # transformer copper losses
        'osl': 0,    # oversizing loss in inverter
        'ttl': 0     # total trafo loss
    }

    return losses

def compile_losses(cumulative_losses, instant_losses, efficiency = 1.0):
    if instant_losses is None:
        return cumulative_losses
    
    for key in instant_losses.keys():
        cumulative_losses[key] += instant_losses[key] * efficiency
        cumulative_losses[key] = round(cumulative_losses[key], 3)

    return cumulative_losses