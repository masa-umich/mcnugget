from synnax.hardware.ni.types import AIVoltageChan, LinScale

def configure_pt_channel(analog_task, row, analog_card):
    pt_channel = AIVoltageChan(port=row["Port"], channel=row["Channel"], device=analog_card.key)
    pt_channel.units = "Volts"
    pt_channel.custom_scale = LinScale(slope=row["Calibration Slope (mV/psig)"] * .0001, 
                                       y_intercept=row["Calibration Offset (V)"], 
                                       pre_scaled_units="Volts", 
                                       scaled_units="PoundsPerSquareInch")
    analog_task.config.channels.append(pt_channel)
    print("Added PT channel", pt_channel.port, pt_channel.channel, pt_channel.device)