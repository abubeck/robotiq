#!/usr/bin/env python

# Software License Agreement (BSD License)
#
# Copyright (c) 2012, Robotiq, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Robotiq, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Copyright (c) 2012, Robotiq, Inc.
# Revision $Id$

"""@package docstring
Command-line interface for receiving and interpreting the status of a S-Model gripper.

This serves as an example for receiving messages from the 'SModelRobotInput' topic using the 'SModel_robot_input' msg type and interpreting the corresponding status of the S-Model gripper.
"""

import roslib; roslib.load_manifest('robotiq_driver')
import rospy
from std_msgs.msg import String
from baseSModel import *
from comModbusTcp import *
from SModelDataType import *
from cob_srvs.srv import Trigger, TriggerResponse
from sensor_msgs.msg import JointState
from robotiq_driver.srv import RobotiqMode, PositionCommand, RobotiqModeResponse, PositionCommandResponse

class SModelDriver:
  initialized = False
  def __init__(self):
    s = rospy.Service('movePosition', PositionCommand, self.moveGripper)
    s2 = rospy.Service('init', Trigger, self.initGripper)
    s3 = rospy.Service('detach', Trigger, self.detachGripper)
    s4 = rospy.Service('changeMode', RobotiqMode, self.changeMode)
    self.js_pub = rospy.Publisher('/joint_states', JointState)

    self.address = rospy.get_param('~ip_address', '192.168.0.1')
    print "Using IP:", self.address

    self.gripper = robotiqBaseSModel()
    self.gripper.client = communication()

  def moveGripper(self, req):
    res = PositionCommandResponse()
    if(self.initialized):
      command = outputMsg()
      command.rACT = 1
      command.rGTO = 1
      command.rSPA = 255
      command.rFRA = 150

      #Move
      if(req.position > 255):
        posi = 255
      elif(req.position < 0):
        posi = 0
      else:
        posi = req.position
      command.rPRA = posi
      print "move command to ", posi
      self.gripper.refreshCommand(command)
      self.gripper.sendCommand()
      res.success = True
      return res
    else:
      res.success = False
      return res

  def changeMode(self, req):
    command = outputMsg()
    command.rACT = 1
    command.rGTO = 1
    command.rSPA = 255
    command.rFRA = 150

    res = RobotiqModeResponse()
    if(self.initialized):

      #Mode
      if(req.mode > 4):
        print "wrong mode"
        res.success = False
        return res
      if(req.mode <= 0):
        print "wrong mode"
        res.success = False
        return res

      command.rMOD = req.mode - 1 

      print "change mode to ",  req.mode - 1
      self.gripper.refreshCommand(command)
      self.gripper.sendCommand()
      res.success = True
      return res
    else:
      res.success = False
      return res

  def initGripper(self, req):
    res = TriggerResponse()
    self.gripper.client.connectToDevice(self.address)

    #reset Gripper
    command = outputMsg()
    command.rACT = 0
    self.gripper.refreshCommand(command)
    self.gripper.sendCommand()
    
    #init Gripper
    command = outputMsg()
    command.rACT = 1
    command.rGTO = 1
    command.rSPA = 255
    command.rFRA = 150
    self.gripper.refreshCommand(command)
    self.gripper.sendCommand()
    self.initialized = True
    res.success.data = True
    return res

  def detachGripper(self, req):
    res = TriggerResponse()
    self.initialized = False
    self.gripper.client.disconnectFromDevice()
    res.success.data = True
    return res


  def run(self):
    if(self.initialized):
      status = self.gripper.getStatus()
      js = JointState()
      js.header.stamp = rospy.Time().now()
      js.name = ["gripperjoint_1", "gripperjoint_2", "gripperjoint_3"]
      js.position = [status.gPOA/255.0, status.gPOB/255.0, status.gPOC/255.0]
      js.velocity = [0.0, 0.0, 0.0]
      js.effort = [status.gCUA*10, status.gCUB*10, status.gCUC*10]
      self.js_pub.publish(js)

if __name__ == '__main__':
  rospy.init_node('SModelDriver')
  driver = SModelDriver()
  #We loop
  while not rospy.is_shutdown():
    driver.run()
    rospy.sleep(0.4)


def SModelStatusListener():
    """Initialize the node and subscribe to the SModelRobotInput topic."""
    

     #Gripper is a S-Model with a TCP connection
    gripper = robotiqBaseSModel()
    gripper.client = communication()

    


    


    #rospy.Subscriber("SModelRobotInput", inputMsg.SModel_robot_input, printStatus)
    #rospy.spin()

def statusInterpreter(status):
    """Generate a string according to the current value of the status variables."""

    output = '\n-----\nS-Model status interpreter\n-----\n'

    #gACT
    output += 'gACT = ' + str(status.gACT) + ': '
    if(status.gACT == 0):
       output += 'Gripper reset\n'
    if(status.gACT == 1):
       output += 'Gripper activation\n'

    #gMOD
    output += 'gMOD = ' + str(status.gMOD) + ': '
    if(status.gMOD == 0):
        output += 'Basic Mode\n'
    if(status.gMOD == 1):
        output += 'Pinch Mode\n'
    if(status.gMOD == 2):
        output += 'Wide Mode\n'
    if(status.gMOD == 3):
        output += 'Scissor Mode\n'

    #gGTO
    output += 'gGTO = ' + str(status.gGTO) + ': '
    if(status.gGTO == 0):
        output += 'Stopped (or performing activation/grasping mode change/automatic release)\n'
    if(status.gGTO == 1):
        output += 'Go to Position Request\n'

    #gIMC
    output += 'gIMC = ' + str(status.gIMC) + ': '
    if(status.gIMC == 0):
        output += 'Gripper is in reset (or automatic release) state. see Fault Status if Gripper is activated\n'
    if(status.gIMC == 1):
        output += 'Activation in progress\n'
    if(status.gIMC == 2):
        output += 'Mode change in progress\n'
    if(status.gIMC == 3):
        output += 'Activation and mode change are completed\n'

    #gSTA
    output += 'gSTA = ' + str(status.gSTA) + ': '
    if(status.gSTA == 0):
        output += 'Gripper is in motion towards requested position (only meaningful if gGTO = 1)\n'
    if(status.gSTA == 1):
        output += 'Gripper is stopped. One or two fingers stopped before requested position\n'
    if(status.gSTA == 2):
        output += 'Gripper is stopped. All fingers stopped before requested position\n'
    if(status.gSTA == 3):
        output += 'Gripper is stopped. All fingers reached requested position\n'

    #gDTA
    output += 'gDTA = ' + str(status.gDTA) + ': '
    if(status.gDTA == 0):
        output += 'Finger A is in motion (only meaningful if gGTO = 1)\n'
    if(status.gDTA == 1):
        output += 'Finger A has stopped due to a contact while opening\n'
    if(status.gDTA == 2):
        output += 'Finger A has stopped due to a contact while closing\n'
    if(status.gDTA == 3):
        output += 'Finger A is at requested position\n'
       
    #gDTB
    output += 'gDTB = ' + str(status.gDTB) + ': '
    if(status.gDTB == 0):
        output += 'Finger B is in motion (only meaningful if gGTO = 1)\n'
    if(status.gDTB == 1):
        output += 'Finger B has stopped due to a contact while opening\n'
    if(status.gDTB == 2):
        output += 'Finger B has stopped due to a contact while closing\n'
    if(status.gDTB == 3):
        output += 'Finger B is at requested position\n'

    #gDTC
    output += 'gDTC = ' + str(status.gDTC) + ': '
    if(status.gDTC == 0):
        output += 'Finger C is in motion (only meaningful if gGTO = 1)\n'
    if(status.gDTC == 1):
        output += 'Finger C has stopped due to a contact while opening\n'
    if(status.gDTC == 2):
        output += 'Finger C has stopped due to a contact while closing\n'
    if(status.gDTC == 3):
        output += 'Finger C is at requested position\n'

    #gDTS
    output += 'gDTS = ' + str(status.gDTS) + ': '
    if(status.gDTS == 0):
        output += 'Scissor is in motion (only meaningful if gGTO = 1)\n'
    if(status.gDTS == 1):
        output += 'Scissor has stopped due to a contact while opening\n'
    if(status.gDTS == 2):
        output += 'Scissor has stopped due to a contact while closing\n'
    if(status.gDTS == 3):
        output += 'Scissor is at requested position\n'

    #gFLT
    output += 'gFLT = ' + str(status.gFLT) + ': '
    if(status.gFLT == 0x00):
        output += 'No Fault\n'
    if(status.gFLT == 0x05):
        output += 'Priority Fault: Action delayed, activation (reactivation) must be completed prior to action\n'
    if(status.gFLT == 0x06):
        output += 'Priority Fault: Action delayed, mode change must be completed prior to action\n'
    if(status.gFLT == 0x07):
        output += 'Priority Fault: The activation bit must be set prior to action\n'
    if(status.gFLT == 0x09):
        output += 'Minor Fault: The communication chip is not ready\n'
    if(status.gFLT == 0x0A):
        output += 'Minor Fault: Changing mode fault, interferences detected on Scissor (for less than 20 sec)\n'
    if(status.gFLT == 0x0B):
        output += 'Minor Fault: Automatic release in progress\n'
    if(status.gFLT == 0x0D):
        output += 'Major Fault: Activation fault, verify that no interference or other error occured\n'
    if(status.gFLT == 0x0E):
        output += 'Major Fault: Changing mode fault, interferences detected on Scissor (for more than 20 sec)\n'
    if(status.gFLT == 0x0F):
        output += 'Major Fault: Automatic release completed. Reset and activation is required\n'

    #gPRA
    output += 'gPRA = ' + str(status.gPRA) + ': '
    output += 'Echo of the requested position for the Gripper (or finger A in individual mode): ' + str(status.gPRA) + '/255\n'

    #gPOA
    output += 'gPOA = ' + str(status.gPOA) + ': '
    output += 'Position of Finger A: ' + str(status.gPOA) + '/255\n'

    #gCUA
    output += 'gCUA = ' + str(status.gCUA) + ': '
    output += 'Current of Finger A: ' + str(status.gCUA * 10) + ' mA\n'

    #gPRB
    output += 'gPRB = ' + str(status.gPRB) + ': '
    output += 'Echo of the requested position for finger B: ' + str(status.gPRB) + '/255\n'

    #gPOB
    output += 'gPOB = ' + str(status.gPOB) + ': '
    output += 'Position of Finger B: ' + str(status.gPOB) + '/255\n'

    #gCUB
    output += 'gCUB = ' + str(status.gCUB) + ': '
    output += 'Current of Finger B: ' + str(status.gCUB * 10) + ' mA\n'

    #gPRC
    output += 'gPRC = ' + str(status.gPRC) + ': '
    output += 'Echo of the requested position for finger C: ' + str(status.gPRC) + '/255\n'

    #gPOC
    output += 'gPOC = ' + str(status.gPOC) + ': '
    output += 'Position of Finger C: ' + str(status.gPOC) + '/255\n'

    #gCUC
    output += 'gCUC = ' + str(status.gCUC) + ': '
    output += 'Current of Finger C: ' + str(status.gCUC * 10) + ' mA\n'

    #gPRS
    output += 'gPRS = ' + str(status.gPRS) + ': '
    output += 'Echo of the requested position for the scissor axis: ' + str(status.gPRS) + '/255\n'

    #gPOS
    output += 'gPOS = ' + str(status.gPOS) + ': '
    output += 'Position of the scissor axis: ' + str(status.gPOS) + '/255\n'

    #gCUS
    output += 'gCUS = ' + str(status.gCUS) + ': '
    output += 'Current of the scissor axis: ' + str(status.gCUS * 10) + ' mA\n'        

    return output
    

