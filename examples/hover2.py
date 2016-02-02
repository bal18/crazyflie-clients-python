import sys
sys.path.append("../lib")

import cflib.crtp
import time
from cflib.crazyflie import Crazyflie

# https://forum.bitcraze.io/viewtopic.php?t=883


# Initialize the low-level drivers (don't list the debug drivers)
cflib.crtp.init_drivers(enable_debug_driver=False)

# test script try at your own risk !!!!

print("Scanning interfaces for Crazyflies...")

available = cflib.crtp.scan_interfaces()

print("Crazyflies found:")
for i in available:
    print i[0]

if len(available) > 0:
    # Create a Crazyflie object without specifying any cache dirs
    cf = Crazyflie()

    def handle_connected(link_uri):
        print("Connected to %s" % link_uri)

        print("Sending thrust 45000")
        cf.commander.send_setpoint(0, 0, 0, 45000)
        time.sleep(0.75)

        print("Stopping thrust; hovering")
        cf.commander.send_setpoint(0, 0, 0, 0)
        cf.param.set_value("flightmode.althold", "True")

    def close_link():
        print("Closing")
        cf.commander.send_setpoint(0, 0, 0, 0)
        time.sleep(0.1)
        cf.close_link()

    # Connect some callbacks from the Crazyflie API
    cf.connected.add_callback(handle_connected)

    link_uri = available[0][0]
    print("Connecting to %s" % link_uri)

    # Try to connect to the Crazyflie
    cf.open_link(link_uri)

    # Variable used to keep main loop occupied until disconnect
    is_connected = True

    try:
        while is_connected:
            cf.commander.send_setpoint(0, 0, 0, 32767)
            time.sleep(0.5)
    except KeyboardInterrupt:
        is_connected = False
        close_link()
else:
    print("No Crazyflies found, cannot run example")