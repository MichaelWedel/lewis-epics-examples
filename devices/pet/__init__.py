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

from collections import OrderedDict

from lewis.core.statemachine import State
from lewis.devices import StateMachineDevice

from lewis.adapters.epics import EpicsInterface, PV


class ActionState(State):
    def __init__(self, duration=5.0, action=None):
        super(ActionState, self).__init__()
        self._duration = duration
        self._action = action
        self._in_state_since = 0.0

    def on_entry(self, dt):
        self._in_state_since = 0.0

    def in_state(self, dt):
        self._in_state_since += dt

        if self._in_state_since >= self._duration:
            self._context.clear_action()

    def on_exit(self, dt):
        self._action()


class DecayState(State):
    def __init__(self, age_rate=0.01, **kwargs):
        super(DecayState, self).__init__()
        self._age_rate = age_rate
        self._rates = kwargs

    def in_state(self, dt):
        for property, rate in self._rates.items():
            current_value = getattr(self._context, property)
            setattr(self._context, property, min(100, max(0, current_value + rate * dt)))

        self._context.age += self._age_rate * dt


class DyingState(DecayState):
    def __init__(self, max_duration=120, age_rate=0.01, **kwargs):
        super(DyingState, self).__init__(age_rate, **kwargs)

        self._max_duration = max_duration
        self._in_state_since = 0

    def on_entry(self, dt):
        self._in_state_since = 0

    def in_state(self, dt):
        DecayState.in_state(self, dt)

        self._in_state_since += dt

        if self._in_state_since >= self._max_duration:
            self._context.set_dead()


class Pet(StateMachineDevice):
    def _initialize_data(self):
        self.energy = 100
        self.tired = 0
        self.bored = 0
        self.clean = 100
        self.age = 0

        self._is_dead = False

        self._action = None

        self._name = None

    def _get_state_handlers(self):
        def do_eat():
            self.energy = min(100, self.energy + 25)
            self.clean = max(0, self.clean - 5)
            self.tired = min(100, self.tired + 5)

        def do_clean():
            self.clean = min(100, self.clean + 45)
            self.tired = min(100, self.tired + 10)
            self.bored = min(100, self.bored + 5)

        def do_sleep():
            self.tired = min(100, self.tired - 75)
            self.energy = max(0, self.energy - 5)
            self.clean = max(0, self.clean - 5)

        def do_play():
            self.bored = max(0, self.bored - 30)
            self.energy = max(0, self.energy - 25)
            self.tired = min(100, self.tired + 15)
            self.clean = max(0, self.clean - 15)

        return {
            'unnamed': State(),

            'happy': DecayState(bored=0.1, tired=0.05, energy=-0.05, clean=-0.1),
            'unhappy': DecayState(bored=0.05, tired=0.1, energy=-0.1, clean=-0.1),

            'action_received': State(),
            'action_completed': State(),

            'eating': ActionState(action=do_eat),
            'cleaning': ActionState(action=do_clean),
            'sleeping': ActionState(action=do_sleep),
            'playing': ActionState(action=do_play),

            'dying': DyingState(bored=0.01, tired=0.01, energy=-0.01, clean=-0.01),
            'dead': State()
        }

    def _get_initial_state(self):
        return 'unnamed'

    def _get_transition_handlers(self):
        return OrderedDict([
            (('unnamed', 'happy'), lambda: self.name is not None),

            (('happy', 'action_received'), lambda: self._action is not None),
            (('unhappy', 'action_received'), lambda: self._action is not None),
            (('dying', 'action_received'), lambda: self._action is not None),

            (('action_received', 'eating'), lambda: self._action == 'eat'),
            (('action_received', 'sleeping'), lambda: self._action == 'sleep'),
            (('action_received', 'cleaning'), lambda: self._action == 'clean'),
            (('action_received', 'playing'), lambda: self._action == 'play'),

            (('eating', 'action_completed'), lambda: self._action is None),
            (('sleeping', 'action_completed'), lambda: self._action is None),
            (('cleaning', 'action_completed'), lambda: self._action is None),
            (('playing', 'action_completed'), lambda: self._action is None),

            (('action_completed', 'happy'), lambda: self.is_happy),
            (('action_completed', 'dying'), lambda: self.is_dying),
            (('action_completed', 'unhappy'), lambda: not self.is_happy),

            (('happy', 'unhappy'), lambda: not self.is_happy),
            (('unhappy', 'happy'), lambda: self.is_happy),
            (('unhappy', 'dying'), lambda: self.is_dying),

            (('dying', 'dead'), lambda: self.is_dead)
        ])

    @property
    def state(self):
        if self._csm.state in ('action_received', 'action_completed'):
            return 'busy'

        return self._csm.state

    def feed(self):
        if self._csm.can('action_received'):
            self._action = 'eat'

    def tuck_in(self):
        if self._csm.can('action_received'):
            self._action = 'sleep'

    def wash(self):
        if self._csm.can('action_received'):
            self._action = 'clean'

    def play(self):
        if self._csm.can('action_received'):
            self._action = 'play'

    def clear_action(self):
        self._action = None

    @property
    def is_happy(self):
        return self.energy > 35 and self.clean > 25 and self.tired < 80 and self.bored < 75

    @property
    def is_dying(self):
        return self.energy < 5 or self.clean < 5 or self.tired > 95

    @property
    def is_dead(self):
        return self._is_dead

    def set_dead(self):
        self._is_dead = True
        self.energy = 0
        self.tired = 100
        self.bored = 100
        self.clean = 0

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        if self._csm.state == 'unnamed':
            self._name = new_name


class PetEpicsInterface(EpicsInterface):
    """
    This is the EPICS interface to a simulated pet. Keep it happy by feeding it, tucking it in,
    whashing it and playing with it or it dies after a while.
    """
    actions = ['none', 'feed', 'tuck_in', 'wash', 'play']

    pvs = {
        'energy': PV('energy', read_only=True, type='int', low=35, lolo=5,
                     doc='Energy level of the pet, should be above 35, 5 is critical.'),
        'tired': PV('tired', read_only=True, type='int', high=80, hihi=95,
                    doc='Tiredness of the pet, should be below 80, 95 is critical.'),
        'bored': PV('bored', read_only=True, type='int', high=75,
                    doc='How bored the pet is. Should be below 75.'),
        'clean': PV('clean', read_only=True, type='int', low=25, lolo=5,
                    doc='Cleanliness of the pet, should be above 25, 5 is critical.'),
        'state': PV('state', read_only=True, type='string',
                    doc='Indicates what the pet is doing at the moment.'),
        'age': PV('age', read_only=True, type='int', unit='m',
                  doc='The age of the pet in months.'),

        'name': PV('name', type='string'),

        'action': PV('action', type='enum', enums=actions)
    }

    last_action = 0

    @property
    def name(self):
        """The name of the pet. Has to be set before the simulation starts."""
        return self._device.name or 'None yet!'

    @name.setter
    def name(self, new_name):
        self._device.name = new_name

    @property
    def action(self):
        """An action to perform. Will make the pet busy for a while"""
        return 0

    @action.setter
    def action(self, new_action):
        if new_action > 0:
            getattr(self._device, self.actions[new_action])()
