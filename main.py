import threading
import time
import ctypes # To cast uint16_t as int16_t
from poll_deye import PollDeye
from simulate_sdm630 import SimulateSdm630


poll_deye = PollDeye("/dev/ttyUSB0")
simulate_sdm630 = SimulateSdm630("/dev/ttyUSB1")

listen_thread = threading.Thread(target=simulate_sdm630.listen, daemon=True)
listen_thread.start()

while True:
    simulate_sdm630.set_register_value(0, poll_deye.get_register(598)) # register 0 / 598: phase A / L1 voltage

    deye_total_apparent_rate = poll_deye.get_register(620)
    simulate_sdm630.set_register_value(18, deye_total_apparent_rate / 3) # register 18 / 620: phase A / L1 CT apparent power

    deye_gen_power = ctypes.c_int16(poll_deye.get_register(667)).value
    deye_pv1 = poll_deye.get_register(672)
    deye_pv2 = poll_deye.get_register(673)
    deye_pv_power = deye_pv1 + deye_pv2
    deye_load_power = poll_deye.get_register(653)
    deye_batt_power = ctypes.c_int16(poll_deye.get_register(590)).value
    deye_available_yield = deye_gen_power + deye_pv_power - max(-deye_batt_power, 0)
    deye_total_use = deye_load_power + max(-deye_batt_power, 0)

    if abs(deye_available_yield - deye_total_use) <= 50: # if our need for additional power is within a margin of 50 Watts..
        growatt_power_adjustment = 20 # ..the Growatt inverter can continue generating the current amount of power (20 means hold the power)
    elif deye_available_yield < deye_total_use: # if the Deye inverter generates less power than we consume..
        growatt_power_adjustment = 35 # ..we want the Growatt inverter to generate more power (35 means increase the power)
    else: # if the Growatt inverter is generating more power than we need..
        growatt_power_adjustment = -35 # ..we want the Growatt inverter to generate less power (-35 means decrease power)

    print("Battery power:\t" + str(deye_batt_power))
    print("Total yield:\t" + str (deye_available_yield))
    print("Total use:\t" + str(deye_total_use))
    print("Additional demand:\t" + str(abs(deye_pv_power - deye_total_use)))

    simulate_sdm630.set_register_value(52, growatt_power_adjustment) # register 52 : Total system power

    simulate_sdm630.set_register_value(70, poll_deye.get_register(609)) # register 70 / 609: Frequency of supply voltages

    simulate_sdm630.set_register_value(342, poll_deye.get_register(504)) # register 342 / 504: Total kwh

    time.sleep(1)
