# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2014 Bitcraze AB
#
#  Crazyflie Nano Quadcopter Client
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA  02110-1301, USA.

"""
Simple scripted escape

https://forum.bitcraze.io/viewtopic.php?t=883

test script try at your own risk !!!!
"""

import time, sys
from threading import Thread

# FIXME: Has to be launched from within the example folder
sys.path.append("../lib")
import cflib
from cfclient.utils.logconfigreader import LogConfig
from cflib.crazyflie import Crazyflie

import logging

logging.basicConfig(level=logging.ERROR)

import logging

logging.basicConfig(level=logging.ERROR)


class Escape:
    """Example that connects to a Crazyflie , escape and then disconnect"""

    def __init__(self, link_uri):
        """ Initialize and run the example with the specified link_uri """

        self._start_alt = 0
        self._alt = 0
        self._takeoff = False

        self._cf = Crazyflie()

        self._cf.connected.add_callback(self._connected)
        self._cf.disconnected.add_callback(self._disconnected)
        self._cf.connection_failed.add_callback(self._connection_failed)
        self._cf.connection_lost.add_callback(self._connection_lost)

        self._cf.open_link(link_uri)

        print("Connecting to %s" % link_uri)

    def _connected(self, link_uri):
        """ This callback is called form the Crazyflie API when a Crazyflie
        has been connected and the TOCs have been downloaded."""

        print("Connected to %s" % link_uri)

        # The definition of the logconfig can be made before connecting
        self._lg_alt = LogConfig(name="altitude", period_in_ms=10)
        self._lg_alt.add_variable("baro.asl", "float")

        # The definition of the logconfig can be made before connecting
        self._lg_stab = LogConfig(name="Stabilizer", period_in_ms=10)
        self._lg_stab.add_variable("stabilizer.roll", "float")
        self._lg_stab.add_variable("stabilizer.pitch", "float")
        self._lg_stab.add_variable("stabilizer.yaw", "float")

        # Adding the configuration cannot be done until a Crazyflie is
        # connected, since we need to check that the variables we
        # would like to log are in the TOC.
        self._cf.log.add_config(self._lg_alt)
        if self._lg_alt.valid:
            # This callback will receive the data
            self._lg_alt.data_received_cb.add_callback(self._alt_log_data)
            # This callback will be called on errors
            self._lg_alt.error_cb.add_callback(self._alt_log_error)
            # Start the logging
            self._lg_alt.start()
        else:
            print("Could not add logconfig since some variables are not in TOC")

        try:
            self._cf.log.add_config(self._lg_stab)
            # This callback will receive the data
            self._lg_stab.data_received_cb.add_callback(self._stab_log_data)
            # This callback will be called on errors
            self._lg_stab.error_cb.add_callback(self._stab_log_error)
            # Start the logging
            self._lg_stab.start()
        except KeyError as e:
            print("Could not start log configuration," \
                  "{} not found in TOC".format(str(e)))
        except AttributeError:
            print("Could not add Stabilizer log config, bad configuration.")


        # Start a separate thread to do the motor test.
        # Do not hijack the calling thread!
        Thread(target=self._do_escape).start()

    def _alt_log_error(self, logconf, msg):
        """Callback from the log API when an error occurs"""
        print("Error when logging %s: %s" % (logconf.name, msg))

    def _alt_log_data(self, timestamp, data, logconf):
        """Callback froma the log API when data arrives"""
        if logconf.name == "altitude":
            if not self._takeoff:
                self._start_alt = data['baro.asl']
                self._takeoff = True
            else:
                self._alt = data['baro.asl']
        print("altitude {} at takeoff".format(self._alt - self._start_alt))

    def _stab_log_error(self, logconf, msg):
        """Callback from the log API when an error occurs"""
        print("Error when logging %s: %s" % (logconf.name, msg))

    def _stab_log_data(self, timestamp, data, logconf):
        """Callback froma the log API when data arrives"""
        print("[%d][%s]: %s" % (timestamp, logconf.name, data))

    def _connection_failed(self, link_uri, msg):
        """Callback when connection initial connection fails (i.e no Crazyflie
        at the speficied address)"""
        print("Connection to %s failed: %s" % (link_uri, msg))

    def _connection_lost(self, link_uri, msg):
        """Callback when disconnected after a connection has been made (i.e
        Crazyflie moves out of range)"""
        print("Connection to %s lost: %s" % (link_uri, msg))

    def _disconnected(self, link_uri):
        """Callback when the Crazyflie is disconnected (called in all cases)"""
        print("Disconnected from %s" % link_uri)

    def _do_escape(self):

        while not self._takeoff:
            pass

        # Unlock startup thrust protection
        self._cf.commander.send_setpoint(0, 0, 0, 0)
        time.sleep(0.1)

        # #                               (Roll, Pitch, Yaw,     Thrust)
        # self._cf.commander.send_setpoint(0, 0, 0, 0.75*64768)
        self._cf.commander.send_setpoint(0, 0, 0, 0.3 * 64768)
        time.sleep(0.2)

        self._cf.commander.send_setpoint(0, 0, 0, 0.6 * 64768)
        time.sleep(0.5)

        self._cf.commander.send_setpoint(0, 0, 0, 0.75 * 64768)
        time.sleep(0.5)

        # self._cf.commander.send_setpoint(0, 0, 0, 0.7 * 64768)
        # time.sleep(0.5)

        #self._cf.commander.send_setpoint(0, 0, 0, 0)
        #
        #self.cf.param.set_value("flightmode.althold", "True")

        # try:
        # while KeyboardInterrupt:
        #     time.sleep(1)
        # except KeyboardInterrupt:
        #     close_link()
        #
        # self._cf.commander.send_setpoint(0, 5, 0, 0.75*64768)
        # # Wait for Crazyflie to reach some altitude, could be replaced by a sleep and needs a timeout!
        # while self._alt < (self._start_alt + 1):
        #     pass

        print("0, Going down!")

        # self._cf.commander.send_setpoint(0, 5, 0, 0.3*64768)
        self._cf.commander.send_setpoint(0, 5, 0, 0.3 * 64768)
        time.sleep(0.3)

        self._cf.commander.send_setpoint(0, 0, 0, 0.55 * 64768)
        # Wait for Crazyflie to come back to 0, could be replaced by a sleep and needs a timeout!
        while self._alt > (self._start_alt + 0.2):
            pass

        self._cf.commander.send_setpoint(0, 0, 0, 0.3 * 64768)
        time.sleep(0.1)

        self._cf.commander.send_setpoint(0, 0, 0, 0)

        # Make sure that the last packet leaves before the link is closed
        # since the message queue is not flushed before closing
        time.sleep(0.1)
        self._cf.close_link()


if __name__ == '__main__':
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)

    # To quickly connect a single Crazyflie
    # le = Escape("radio://0/45/2M")

    # Or, to scan for Crazyflies and use the first one found
    print("Scanning interfaces for Crazyflies...")
    available = cflib.crtp.scan_interfaces()
    print("Crazyflies found:")
    for i in available:
        print(i[0])

    if len(available) > 0:
        le = Escape(available[0][0])
    else:
        print("No Crazyflies found, cannot run example")
