from synnax.control.controller import Controller
from mclib.config import Config

def open_vlv(ctrl: Controller, config: Config, vlv_name: str) -> bool:
    """
    Helper function to open a valve only if not already open
    Considers the valve's Normally Open (NO) or Normally Closed (NC) state.
    """
    state_name: str = vlv_name.replace("vlv", "state")
    current_power = ctrl.get(state_name)
    if current_power is None:
        raise Exception(f"Could not get state of valve: {vlv_name}, is the valve defined?")
    
    is_nc = config.is_vlv_nc(vlv_name)
    # If it is NC (Normally Closed), we need to power it (True) to open it.
    # If it is NO (Normally Open), we need to unpower it (False) to open it.
    target_power = is_nc
    
    if current_power == target_power:
        return False
        
    ctrl[vlv_name] = target_power
    return True

def close_vlv(ctrl: Controller, config: Config, vlv_name: str) -> bool:
    """
    Helper function to close a valve only if not already closed
    Considers the valve's Normally Open (NO) or Normally Closed (NC) state.
    """
    state_name: str = vlv_name.replace("vlv", "state")
    current_power = ctrl.get(state_name)
    if current_power is None:
        raise Exception(f"Could not get state of valve: {vlv_name}, is the valve defined?")
        
    is_nc = config.is_vlv_nc(vlv_name)
    # If it is NC (Normally Closed), we need to unpower it (False) to close it.
    # If it is NO (Normally Open), we need to power it (True) to close it.
    target_power = not is_nc
    
    if current_power == target_power:
        return False
        
    ctrl[vlv_name] = target_power
    return True

def STATE(valve: str) -> str:
    return valve.replace("vlv", "state")
