# Copyright © 2020 Yannick Gingras <ygingras@ygingras.net>

# This file is part of Revengate.

# Revengate is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Revengate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Revengate.  If not, see <https://www.gnu.org/licenses/>.

""" Actors are everyone moving and interacting with the world: beasts, 
monsters, characters, etc. 
"""

import random
from .weapons import Hit, Events, HealthEvent, Condition, Weapon, DmgType

SIGMA = 0.125 # std. dev. for a normal distribution more or less contained in 0..1
MU = 0.5 # average of the above distribution


class Actor(object):
    """ Base class of all actors. """
    # everyone defaults to 35% more damage with a critical hit
    critical_mult = 0.35 
    
    def __init__(self, health, armor, strength, agility):
        super(Actor, self).__init__()
        self.health = health
        self.armor = armor

        # main attributes
        self.strength = strength
        self.agility = agility

        self.resistances = set()
        self.weapon = None

        # taxon and identifiers
        self.species = None
        self.role = None
        self.rank = None
        self.name = None

        # turns logic
        self.initiative = random.random()
        self.engine = None
        self._last_update = None # last time we computed conditions and regen
        self.conditions = [] # mostly stuff that does damage over time

    def set_engine(self, engine):
        """ Finalize the registration with a game engine. """
        self.engine = engine
        self._last_update = engine.current_turn

    def update(self):
        """ 
        Do the update for all the turns since the last update.

        Return the summary of health changes.
        """
        # Actors are only update on the current level.  Upon revisiting a level, 
        # the updates for all missed turns are computed.
        if self.engine is None:
            raise RuntimeError("Actors must be registered with an engine before"
                               " performing turn updates.")
        events = Events()
        for t in range(self._last_update or 0, self.engine.current_turn + 1):
            events.add(self._update_one(t))
        return events
    
    def _update_one(self, turn):
        """
        Compute the effect of all over-time conditions for one turn.
        
        Return the summary of health changes.
        """
        events = Events()
        for cond in self.conditions:
            if cond.start <= turn <= cond.stop:
                self.health += cond.h_delta
                events.add(HealthEvent(self, cond.h_delta))
        self.conditions = [c for c in self.conditions if c.stop > turn]
        self._last_update = turn
        return events or None

    def __str__(self):
        if self.name:
            if self.rank:
                return f"{self.rank} {self.name}"
            return self.name
        if self.species:
            if self.rank or self.role:
                qual = self.rank or self.role
                return f"the {self.species} {qual}"
            return f"the {self.species}"
        if self.rank:
            return f"the {self.rank}"
        if self.role:
            return f"the {self.role}"
        order = self.__class__.__name__.lower()
        return f"the {order}"

    def attack(self, foe):
        """ Do all the stikes allowed in one turn against foe. """
        if self.weapon:
            return Events(self.strike(foe, self.weapon))
        else:
            return None

    def strike(self, foe, weapon):
        """ Try to hit foe, another actor, with weapon. 
        Automatically adjust foe's health when there is a hit. """
        crit = False

        # to-hit roll
        roll = random.normalvariate(MU, SIGMA)
        if roll < foe.get_evasion():
            return None  # miss!
        dmg = self.get_damage(weapon)

        if roll > MU+2*SIGMA:
            # critical hit!
            crit = True
            dmg *= (1+self.critical_mult)

        dmg = foe.take_damage(weapon, dmg)
        return Hit(foe, self, weapon, dmg, crit)

    def take_damage(self, injurious, dmg):
        """ 
        Receive `dmg` damage point from something injurious.  Compute armor 
        protection, resistances, and weaknesses; update health; return how many effective 
        damage were applied. 
        """
        if injurious.dmg_type in self.resistances:
            dmg *= 0.5 # 50% less damage if you have a resistance
        dmg = round(max(0, dmg - self.armor))
        self.health -= dmg
        
        # damage over time effects
        for effect in injurious.effects:
            h_delta = -effect.damage
            if effect.dmg_type in self.resistances:
                h_delta *= 0.5
            start = self.engine.current_turn + 1
            if isinstance(effect.duration, int):
                stop = start + effect.duration
            else:
                stop = start + random.randint(*effect.duration)
            cond = Condition(effect, start, stop, h_delta)
            self.conditions.append(cond)
        return dmg

    def get_evasion(self):
        # TODO: check for incapacitation
        return self.agility

    def get_damage(self, weapon):
        """ Return how much damage the actor can do with a given weapon taking 
        into account procificency and incapacitation. """

        # TODO: check for proficiency
        dmg = weapon.damage
        return (1 + self.strength - MU) * dmg * random.random()


class Monster(Actor):
    """ Monsters follow their instinct; they do not posses soffisticated 
    aspirations nor ethics. """
    def __init__(self, health, armor, strength, agility):
        super(Monster, self).__init__(health, armor, strength, agility)
        

class Character(Actor):
    """ Characters are everyone smart enough to become angry at something.  
    Most characters can use equipment. """
    def __init__(self, health, armor, strength, agility, intelligence):
        super(Character, self).__init__(health, armor, strength, agility)
        self.intelligence = intelligence
        

class Humanoid(Character):
    """ Your average human shapped creature. 
    Most creatures of that shape know how to throw a punch. """
    def __init__(self, health, armor, strength, agility, intelligence, fist_r=4, fist_l=None):
        super(Humanoid, self).__init__(health, armor, strength, agility, intelligence)
        if fist_r:
            self.fist_r = Weapon("fist", fist_r, DmgType.IMPACT)
        else:
            self.fist_r = None

        if fist_l:
            self.fist_l = Weapon("fist", fist_l, DmgType.IMPACT)
        else:
            self.fist_l = None
            
    def attack(self, foe):
        if self.weapon:
            return Events(self.strike(foe, self.weapon))
        else:
            hits = Events()
            if self.fist_r:
                hits.add(self.strike(foe, self.fist_r))
            if self.fist_l:
                hits.add(self.strike(foe, self.fist_l))
            return hits or None
