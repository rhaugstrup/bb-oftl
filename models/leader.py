
from google.appengine.ext import db
from models import Player, Team, CoachStats, Coach

class CoachLeader(db.Model):
  # key_name = title
  display_order = db.IntegerProperty()
  top_text      = db.StringProperty()
  formula       = db.StringProperty()

  @staticmethod
  def init():
    for top_text, key_name, display_order, formula in [
        ('Best', 'Record',  1, "AWP * 1000"),
        ('Most', 'Matches', 2, "Pl"),
        ('Most', 'Silverware', 3, "TPts"),
        ('Top', 'Offense',  4, "50*TD + 3*R + 3*P + YR + YP -250*IA - 150*Pl"),
        ('Top', 'Defense',  5, "250*I + 5*T - 50*TDA - YRA - YPA + 150*Pl"),
        ('Top', 'Violence', 6, "100*K + 25*C + 10*KO +S - 125*Pl"),
        ('Most', 'Nuffled', 7, "100*KA + 25*CA + 250*IA + 50*(TDA-TD) + 25*CA + 5*TA - 175*Pl")]:
      CoachLeader(
          key_name      = key_name,
          top_text      = top_text,
          display_order = display_order,
          formula       = formula).put()

  def get_score(self, coach_stats):
    score = -10000
    if coach_stats.matches >= 20:
      score =  int(eval(self.formula, {
        "AWP":    coach_stats.awp,
#      "Rating": coach_stats.glicko_r,
        "TPts":   coach_stats.tpts,
        "Pl":     coach_stats.matches,
        "TD":     coach_stats.tds_for,
        "R":      coach_stats.rec_for,
        "YR":     coach_stats.ryards_for,
        "P":      coach_stats.passes_for,
        "YP":     coach_stats.pyards_for,
        "K":      coach_stats.kills_for,
        "C":      coach_stats.cas_for,
        "KO":     coach_stats.ko_for,
        "S":      coach_stats.stun_for,
        "T":      coach_stats.tckl_for,
        "I":      coach_stats.int_for,
        "TDA":    coach_stats.tds_against,
        "YRA":    coach_stats.ryards_against,
        "YPA":    coach_stats.pyards_against,
        "KA":      coach_stats.kills_against,
        "CA":      coach_stats.cas_against,
        "KOA":     coach_stats.ko_against,
        "SA":      coach_stats.stun_against,
        "TA":      coach_stats.tckl_against,
        "IA":      coach_stats.int_against,
        }))
    return score

class TeamLeader(db.Model):
  # key_name = title
  display_order = db.IntegerProperty()
  top_text      = db.StringProperty()
  formula       = db.StringProperty()

  @staticmethod
  def init():
    for top_text, key_name, display_order, formula in [
        ('Best', 'Record',  1, "AWP * 1000"),
        ('Highest', 'Rating', 2, "Rating"),
        ('Most', 'Silverware', 3, "TPts"),
        ('Top', 'Offense',  4, "50*TD + 10*R + 5*P + YR + YP - 150*Pl"),
        ('Top', 'Defense',  5, "100*I + 20*T - 50*TDA - YRA - YPA + 50*Pl"),
        ('Top', 'Violence', 6, "100*K + 25*C + 10*KO - 150*Pl")]:
      TeamLeader(
          key_name      = key_name,
          top_text      = top_text,
          display_order = display_order,
          formula       = formula).put()

  def get_score(self, team):
    return int(eval(self.formula, {
      "AWP":    team.awp,
      "Rating": team.glicko_r,
      "TPts":   team.tpts,
      "Pl":     team.matches,
      "TD":     team.tds_for,
      "R":      team.rec_for,
      "YR":     team.ryards_for,
      "P":      team.passes_for,
      "YP":     team.pyards_for,
      "K":      team.kills_for,
      "C":      team.cas_for,
      "KO":     team.ko_for,
      "S":      team.stun_for,
      "T":      team.tckl_for,
      "I":      team.int_for,
      "TDA":    team.tds_against,
      "YRA":    team.ryards_against,
      "YPA":    team.pyards_against,
      }))


class PlayerLeader(db.Model):
  # key_name = title
  display_order = db.IntegerProperty()
  formula       = db.StringProperty()
  top_text      = db.StringProperty()

  @staticmethod
  def init():
    for top_text, key_name, display_order, formula in [
          ('Most',    'Legendary', 4, "SPP"),
          ('Highest', 'Salary',    5, "Value"),
          ('Top',     'Scorer',    1, "150*TD - 50*Pl"),
          ('Top',     'Playmaker', 2, "50*P + 5*YP - 50*Pl"),
          ('Top',     'Blocker',   3, "100*C + 25*KO + 10*S + 25*T - 50*Pl")]:
      PlayerLeader(
          key_name      = key_name,
          top_text      = top_text,
          display_order = display_order,
          formula       = formula).put()

  def get_score(self, player):
    return int(eval(self.formula, {
      "SPP":   player.spp,
      "TD":    player.tds_for,
      "P":     player.passes_for,
      "YP":    player.pyards_for,
      "K":     player.kills_for,
      "C":     player.cas_for,
      "KO":    player.ko_for,
      "S":     player.stun_for,
      "T":     player.tckl_for,
      "Pl":    player.played,
      "Value": player.value,
      }))

class CoachLeaderStanding(db.Model):
  # key_name = coach_key_name
  # parent = CoachLeader
  score    = db.IntegerProperty()
  coach_stats  = db.ReferenceProperty(CoachStats)
  
class TeamLeaderStanding(db.Model):
  # key_name = team_key_name
  # parent = TeamLeader
  score    = db.IntegerProperty()
  team     = db.ReferenceProperty(Team)


class PlayerLeaderStanding(db.Model):
  # key_name = player_key_name
  # parent = PlayerLeader
  score    = db.IntegerProperty()
  player   = db.ReferenceProperty(Player)


