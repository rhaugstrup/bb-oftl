
# order matters!
from coach import *
from team import *
from player import *
from leader import *
from match import *
from tournament import *

def init():
  CoachLeader.init()
  TeamLeader.init()
  PlayerLeader.init()
  Skill.init()
  Race.init()
  Position.init()
  Injury.init()

