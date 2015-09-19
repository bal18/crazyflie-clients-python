import logging
import sys
from threading import Thread
import time

sys.path.append("../lib")

from cflib.crazyflie import Crazyflie
from cflib import crtp

# test script try at your own risk !!!!
class Hover:

   def __init__(self):
      self.m_bShuttingDown = False
      self.m_CrazyFlie = None

   def Run(self):
      logging.basicConfig()
      logging.getLogger().setLevel(logging.INFO)
      #logging.getLogger().setLevel(logging.DEBUG)

      logging.info("Initializing drivers.")
      # Init drivers
      crtp.init_drivers()
      availableLinks = crtp.scan_interfaces()
      logging.info("Available links: %s"%(availableLinks))
      logging.info("Initializing Crazyflie.")
      self.m_CrazyFlie = Crazyflie(ro_cache="cachero", rw_cache="cacherw")

      logging.info("Setting radio link.")
      if(len(availableLinks) == 0):
         logging.error("Error, no links.  Aborting.")
         return

      linkUri = availableLinks[0][0]

      self.m_CrazyFlie.connected.add_callback(self.OnConnected)
      self.m_CrazyFlie.open_link(linkUri)

      try:
         while not self.m_bShuttingDown:
            time.sleep(0.1)
      except:
         logging.error("Shutting down due to exception.")
         self.m_bShuttingDown = True
         self.m_CrazyFlie.close_link()

   def OnConnected(self,linkUri):
      logging.info("OnConnectSetupFinished")

      def Pulse():
         while not self.m_bShuttingDown:
            roll = 0
            pitch = 0
            yawrate = 0
            thrust = 32000
            self.m_CrazyFlie.commander.send_setpoint(roll, pitch, yawrate, thrust)
            time.sleep(2)

      Pulse()


Hover().Run()