# -*- coding: utf-8 -*-
# *********************************************************************
# lewis epics examples - examples for EPICS devices in Lewis
# Copyright (C) 2017 European Spallation Source ERIC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# *********************************************************************

from lewis.examples.example_motor import SimulatedExampleMotor
from lewis.adapters.epics import EpicsInterface, PV
from lewis.core.utils import check_limits


class ExampleMotorEpicsInterface(EpicsInterface):
    pvs = {
        'Pos': PV('position', read_only=True, unit='mm', doc='Current position of the motor'),
        'Tgt': PV('target', meta_data_property='target_meta', unit='mm',
                  doc='Target of motor. Changing the target automatically moves the motor.'),
        'Spd': PV('speed', unit='mm/s', lolim='0', hilim='10',
                  doc='Speed of motor in mm/s'),
        'Stop': PV('stop', type='int', lolim=1, hilim=1),
        'Stat': PV('state', type='string',
                   doc='Current state of the motor, either idle or moving.')
    }

    target_lolim = 10
    target_hilim = 200

    @property
    def target(self):
        return self._device.target

    @target.setter
    @check_limits('target_lolim', 'target_hilim')
    def target(self, new_target):
        self._device.target = new_target

    @property
    def target_meta(self):
        return {
            'lolim': self.target_lolim,
            'hilim': self.target_hilim
        }

    @property
    def speed(self):
        return self._device.speed

    @speed.setter
    @check_limits(0, 10)
    def speed(self, new_speed):
        self._device.speed = new_speed

    @property
    def stop(self):
        """
        Write 1 to this PV to stop the motor. Other values are silently ignored.
        """
        return 0

    @stop.setter
    def stop(self, stop_value):
        if stop_value == 1:
            self._device.stop()
