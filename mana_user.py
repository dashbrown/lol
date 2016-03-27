from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np
import sys

class Ability(object):
  
  def __init__(self, cooldown, cost, base, ratio, name):
    self.cooldown = cooldown
    self.cost = cost
    self.name = name
    self.base = base
    self.ratio = ratio
    self.counter = sys.maxint
    self.time_interval = 0.1

  def apply_cdr(self, cdr):
    return (1 - cdr) * self.cooldown;

  def damage(self, ap):
    return self.base + ap * self.ratio

  def increment_counter(self):
    self.counter += self.time_interval


class Champion(object):

  def __init__(self, name, mana, regen, abilities):
    self.name = name
    self.max_mana = mana
    self.current_mana = self.max_mana
    self.base_regen = regen
    self.regen = self.base_regen
    self.regen_counter = 0
    self.cdr = 0
    self.oom = False
    self.abilities = abilities
    self.casts = defaultdict(int)
    self.time_interval = 0.1
    self.ap = 0
    self.mpen = 0
    self.damage_done = 0
    self.time = 0
    self.log = [(self.time, self.damage_done)]
    self.target = Target_Dummy(0, 0, 2000)

  def set_target(self, target):
    self.target = target

  def cast_ability(self, ability):
    # print "Ability: ", ability.name
    ability.counter = 0
    self.current_mana -= ability.cost
    self.casts[ability.name] += 1
    ability_damage = ability.damage(self.ap)
    target_damage_taken = \
      self.target.take_damage(ability_damage, self.mpen, 'magic')
    self.damage_done += target_damage_taken

  def update_log(self):
    self.time += self.time_interval
    if np.allclose(self.time % .5, 0) or np.allclose(self.time % 0.5, 0.5):
      self.log.append((self.time, self.damage_done))

  def increment_ability_counters(self):
    for ability in self.abilities:
      ability.increment_counter()

  def cast_abilities(self):
    for ability in self.abilities:
      if ability.counter >= ability.apply_cdr(self.cdr):
        if self.current_mana - ability.cost <= 0:
          self.oom = True
          # print "Failed to cast: ", ability.name
        else:
          self.cast_ability(ability)

  def regen_mana(self):
    self.regen_counter += self.time_interval
    if self.regen_counter >= .5:
      self.current_mana += self.regen / 10.0
      self.regen_counter = 0
      # print "Mana: ", self.current_mana

  def missing_mana(self):
    return self.max_mana - self.current_mana

  def get_unzipped_log(self, title = ""):
    if title == "":
      title = self.name
    xs, ys = [], []
    for time, damage in self.log:
      xs.append(time)
      ys.append(damage)
    # build_plot(xs, ys, "time (s)", "damage", title, "", "", title + ".png")
    return xs, ys


  def step(self):
    self.increment_ability_counters()
    self.cast_abilities()
    self.regen_mana()
    self.update_log()


class Target_Dummy(object):

  def __init__(self, armor, mr, health):
    self.armor = armor
    self.mr = mr
    self.health = health

  def take_damage(self, damage, pen, type):
    if type == 'magic':
      multiplier = 100.0 / (100 + self.mr - pen)
    elif type == 'phys':
      multiplier = 100.0 / (100 + self.armor - pen)
    self.health -= multiplier * damage
    return multiplier * damage


class Simulation(object):

  def __init__(self, champion, items, post_items, ti, max_time, filename="ignore"):
    self.champion = champion
    self.timer = 0
    self.post_items = post_items
    self.items = items
    self.time_interval = ti
    self.champion.time_interval = ti
    self.max_time = max_time
    self.filename = filename
    for ability in self.champion.abilities:
      ability.time_interval = ti

  def run(self):
    for item in self.items:
      item(self.champion)
    while not self.champion.oom and self.timer < self.max_time:
      self.timer += self.time_interval
      # if self.timer % 1 < .0001:
        # print "Time: ", self.timer
      self.champion.step()
      for item in self.post_items:
        item(self.champion)
    items = []
    for item in self.items + self.post_items:
      # print item.__name__
      items.append(item.__name__)
    # print "Time: ", self.timer, " Items: ", items, "\nCasts: \nQ: %s"
    print "    Time: {0}\n    Items: {1}\n    Casts:\n\t    Q: {2}\n\t    W: {3}\n\t    E: {4}\n\t    R: {5}\n\n"\
    .format(self.timer, items, self.champion.casts['q'], self.champion.casts['w'], \
    self.champion.casts['e'], \
    self.champion.casts['r'])
    return self.champion.get_unzipped_log()
    # self.champion.build_graph(title=self.filename)

def build_plot(xs, ys, x, y, t, m1, m2, filename):
  plt.clf()
  plt.plot(xs,ys)
  plt.xlabel(x)
  plt.ylabel(y)
  plt.title(t)
  plt.text(2500, ys[0] + 50, m1)
  plt.text(1250, ys[-1]/2+50, m2)
  plt.savefig(filename)

def RoA(champion):
  champion.max_mana += 800
  champion.current_mana += 800
  champion.ap += 120

def Athenes(champion):
  champion.regen += champion.base_regen
  champion.cdr += .2
  champion.ap += 60

def Ludens(champion):
  champion.ap += 100

def Rylais(champion):
  champion.ap += 100

def Deathcap(champion):
  champion.ap += 120
  champion.ap *= 1.35

def Sorc_boots(champion):
  champion.mpen += 15

def Cdr_boots(champion):
  champion.cdr += 0.1

def Athenes_post(champion):
  if champion.regen_counter == 0:
    missing = champion.missing_mana() * .002
    champion.current_mana += missing
    # print "Athenes: ", missing
    champion.current_mana = min(champion.current_mana, champion.max_mana)


if __name__ == '__main__':
  
  # q = Ability(3, 50, 180, 0.5, 'q')
  # w = Ability(9, 110, 250, 0.7, 'w')
  # e = Ability(9, 60, 180, 0.3, 'e')
  # r = Ability(90, 150, 0, 0, 'r')
  # abilities = [q,w,e,r]

  # ori = Champion('ori', 1184, 19.6, .4, abilities)
  # sim = Simulation(ori, [Athenes], [Athenes_post], 0.1)
  # sim.run()

  # q = Ability(3, 50, 180, 0.5, 'q')
  # w = Ability(9, 110, 250, 0.7, 'w')
  # e = Ability(9, 60, 180, 0.3, 'e')
  # r = Ability(90, 150, 0, 0, 'r')
  # abilities = [q,w,e,r]

  # ori = Champion('ori', 1184, 19.6, .4, abilities)
  # sim = Simulation(ori, [RoA, Athenes], [], 0.1)
  # sim.run()

  q = Ability(3, 50, 180, 0.5, 'q')
  w = Ability(9, 110, 250, 0.7, 'w')
  e = Ability(9, 60, 180, 0.3, 'e')
  r = Ability(90, 150, 0, 0, 'r')
  abilities = [q,w,e,r]

  ori = Champion('ori', 1184, 19.6, abilities)
  ori.set_target(Target_Dummy(100,100,10000))
  sim = Simulation(ori, \
    [RoA, Athenes, Ludens, Rylais, Deathcap, Sorc_boots], [Athenes_post], \
    0.1, 600)
  sorcxs, sorcys = sim.run()

  q = Ability(3, 50, 180, 0.5, 'q')
  w = Ability(9, 110, 250, 0.7, 'w')
  e = Ability(9, 60, 180, 0.3, 'e')
  r = Ability(90, 150, 0, 0, 'r')
  abilities = [q,w,e,r]

  ori = Champion('ori', 1184, 19.6, abilities)
  ori.set_target(Target_Dummy(100,100,10000))
  sim = Simulation(ori, \
    [RoA, Athenes, Ludens, Rylais, Deathcap, Cdr_boots], [Athenes_post], \
    0.1, 600)
  cdrxs, cdrys = sim.run()

  plt.clf()
  fig = plt.figure()
  ax1 = fig.add_subplot(111)
  ax1.scatter(sorcxs, sorcys, s=10, c='b', marker="s", label='sorcs')
  ax1.scatter(cdrxs,cdrys, s=10, c='r', marker="o", label='cdr')
  plt.legend(loc='upper left');
  plt.savefig("sorcs_vs_cdr.png")

  deltaxs, deltays = [], []
  for i in xrange(min(len(cdrxs), len(sorcxs))):
    deltaxs.append(cdrxs[i])
    deltays.append(sorcys[i] - cdrys[i])
  plt.clf()
  plt.plot(deltaxs, deltays)
  plt.plot(deltaxs, [0]*len(deltaxs))
  plt.xlabel("time")
  plt.ylabel("sorcs - cdr")
  plt.title("sorcs vs cdr delta")
  plt.savefig("sorcs_vs_cdr_delta.png")

