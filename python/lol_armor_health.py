# import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.optimize import fmin_slsqp
import numpy as np
# from mpl_toolkits.mplot3d import Axes3D

# xs = range(500)
# mults = [100.0 / (100 + x) for x in xs]
# ys = [1 / mult for mult in mults]

# plt.plot(xs,ys)
# plt.xlabel("armor/mr")
# plt.ylabel("effective health multiplier")
# plt.show()

def effective_health(health, armor):
  return health * (100 + armor) / 100.0

def health_to_armor_normalized(health):
  return 15 * health / 112.5 - 100

def health_to_armor_normalized_mixed(health):
  return 7.5 * health / 112.5 - 100

def health_to_mr_normalized_mixed(health):
  return 12.5 * health / 168.75 - 100

def health_to_mr_normalized(health):
  return 25 * health / 168.75 - 100 

def health_to_armor_mr_custom(health, bonus_health, bonus_armor):
  return float(health) * bonus_armor / bonus_health - 100

def plot_normalized_health_vs_armor():
  xs = range(500,4000)
  ys = [health_to_armor_normalized(x) for x in xs]
  build_plot(xs, ys, "Health", "Armor", "Normalized Health vs Armor",
            "Build Armor", "Build Health", "health_vs_armor_normalized.png")

def plot_normalized_health_vs_mr():
  xs = range(500,4000)
  ys = [health_to_mr_normalized(x) for x in xs]
  build_plot(xs, ys, "Health", "Magic Resist", "Normalized Health vs MR",
            "Build MR", "Build Health", "health_vs_mr_normalized.png")

def plot_ruby_crystal_vs_cloth_armor():
  xs = range(500,4000)
  ys = [health_to_armor_mr_custom(x, 150, 15) for x in xs]
  build_plot(xs, ys, "Health", "Armor", "Ruby Crystal vs Cloth Armor",
            "Build Cloth Armor", "Build Ruby Crystal", "ruby_crystal_vs_cloth_armor.png")

def plot_ruby_crystal_vs_cloth_armor_mixed():
  xs = range(500,4000)
  ys = [health_to_armor_mr_custom(x, 150, 7.5) for x in xs]
  build_plot(xs, ys, "Health", "Armor", "Ruby Crystal vs Cloth Armor, Mixed Damage",
            "Build Cloth Armor", "Build Ruby Crystal", "ruby_crystal_vs_cloth_armor_mixed.png")

def plot_ruby_crystal_vs_null_magic_mantle():
  xs = range(500,4000)
  ys = [health_to_armor_mr_custom(x, 150, 25) for x in xs]
  build_plot(xs, ys, "Health", "Magic Resist", "Ruby Crystal vs Null-Magic Mantle",
            "Build Null-Magic Mantle", "Build Ruby Crystal", "ruby_crystal_vs_null_magic_mantle.png")


def apply_resistance(resistance, dps):
  return dps * 100.0 / (100 + resistance)

def time_to_die(health, armor, mr, pdps, mdps):
  health = max(health, 0)
  armor = max(armor, 0)
  mr = max(mr, 0)
  mdps_after_mr = apply_resistance(mr, mdps)
  pdps_after_armor = apply_resistance(armor, pdps)
  total_dps = mdps_after_mr + pdps_after_armor
  # return total_dps
  return health / total_dps

def all_above_zero(x,*args):
  return [x[0], x[1], x[2]]

def spend_gold_currey(i):
  def spend_gold(x,*args):
    return [2.67*x[0] + 20*x[1] + 18*x[2] - i]
  return spend_gold

def spend_gold_currey_norm(i):
  def spend_gold(x,*args):
    return [3*x[0] + 30*x[1] + 18*x[2] - i]
  return spend_gold

def ttd(x, sign = 1.0, p = 1.0, m = 1.0):
  return sign * time_to_die(x[0], x[1], x[2], p, m)

def ttd_jac(x, sign = 1.0, p = 1.0, m = 1.0):
  x[0] = max(x[0],0)
  x[1] = max(x[1],0)
  x[2] = max(x[2],0)
  dh = sign * 1.0 / (100 * (p / (100 + x[1]) + m / (100 + x[2])))
  da = sign * p * (100 + x[2])**2 * x[0] / \
      (100 * (m * (100 + x[1]) + p * (100 + x[2]))**2)
  dm = sign * m * (100 + x[1])**2 * x[0] / \
      (100 * (m * (100 + x[1]) + p * (100 + x[2]))**2)
  return np.array([dh, da, dm])

def run_ttd(range, p=1.0, m=1.0, spend_gold = spend_gold_currey):
  xs = []
  ys = []
  zs = []
  gs = []
  for i in range:
    spend_all_gold = spend_gold(i)
    res = fmin_slsqp(ttd,[1400,0,0],args=(-1,p,m,),
          ieqcons=[all_above_zero,],
          eqcons=[spend_all_gold,],
          disp=False)
    xs.append(res[0])
    ys.append(res[1])
    zs.append(res[2])
    gs.append(i)
  return xs, ys, zs, gs

def build_plot(xs, ys, x, y, t, m1, m2, filename):
  plt.clf()
  plt.plot(xs,ys)
  plt.xlabel(x)
  plt.ylabel(y)
  plt.title(t)
  plt.text(2500, ys[0] + 50, m1)
  plt.text(1250, ys[-1]/2+50, m2)
  plt.savefig(filename)

def build_file(p,m,norm = True):
  pdps = p
  mdps = m
  spend_gold = spend_gold_currey if not norm else spend_gold_currey_norm
  xs, ys, zs, gs = run_ttd(xrange(500,20000,250), pdps, mdps, spend_gold)
  xs = [int(x) for x in xs]
  ys = [int(y) for y in ys]
  zs = [int(z) for z in zs]
  with open("../txt/md_norm_health_armor_mr_" + str(pdps) + "_" + str(mdps) + ".md","w") as f:
    f.write("| Health | Armor | MR | Gold |\n")
    f.write("|:---:|:---:|:---:|:---:|\n")
    for i in xrange(len(xs)):
      if xs[i] >= 0 and ys[i] >= 0 and zs[i] >= 0:
        f.write("|" + str(xs[i]) + \
                "|" + str(ys[i]) + \
                "|" + str(zs[i]) + \
                "|" + str(gs[i]) + "|\n")  

if __name__ == '__main__':

  build_file(1,1)
  build_file(1,0)
  build_file(0,1)
  build_file(2,1)
  build_file(1,2)
  build_file(3,1)
  build_file(1,3)

















