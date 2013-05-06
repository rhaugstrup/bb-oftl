
from google.appengine.ext import db
from google.appengine.api import urlfetch
import math, logging, urllib

import models


class Race(db.Model):
  # key_name = racename

  @staticmethod
  def init():
    for key_name in [
        'Humans',
        'Dwarves',
        'Skaven',
        'Orcs',
        'Lizardmen',
        'Goblins',
        'Wood Elves',
        'Chaos',
        'Dark Elves',
        'Undead',
        'Halflings',
        'Norse',
        'Amazon',
        'Pro Elves',
        'High Elves',
        'Khemri',
        'Necromantic',
        'Nurgle',
        'Ogre',
        'Vampire',
        'Chaos Dwarves',
        'Khorne',
        'Underworld']:
      Race(key_name = key_name).put()

  def get_image_src(self, thumb = False):
    subdir = "thumb/" if thumb else ""
    return "images/races/%s%s.png" % (subdir,
        self.key().name().lower().replace(" ", ""))


class TeamStats(db.Model):
  tv_for           = db.IntegerProperty(default=0)
  tv_against       = db.IntegerProperty(default=0)
  tds_for          = db.IntegerProperty(default=0)
  tds_against      = db.IntegerProperty(default=0)
  passes_for       = db.IntegerProperty(default=0)
  passes_against   = db.IntegerProperty(default=0)
  pyards_for       = db.IntegerProperty(default=0)
  pyards_against   = db.IntegerProperty(default=0)
  rec_for          = db.IntegerProperty(default=0)
  rec_against      = db.IntegerProperty(default=0)
  ryards_for       = db.IntegerProperty(default=0)
  ryards_against   = db.IntegerProperty(default=0)
  int_for          = db.IntegerProperty(default=0)
  int_against      = db.IntegerProperty(default=0)
  kills_for        = db.IntegerProperty(default=0)
  kills_against    = db.IntegerProperty(default=0)
  cas_for          = db.IntegerProperty(default=0)
  cas_against      = db.IntegerProperty(default=0)
  ko_for           = db.IntegerProperty(default=0)
  ko_against       = db.IntegerProperty(default=0)
  stun_for         = db.IntegerProperty(default=0)
  stun_against     = db.IntegerProperty(default=0)
  tckl_for         = db.IntegerProperty(default=0)
  tckl_against     = db.IntegerProperty(default=0)

  def accumulate(self, team_stats):
    for property in TeamStats.properties():
      setattr(self, property,
          getattr(self, property) +
          getattr(team_stats, property))

  def reset(self):
    for property in TeamStats.properties():
      setattr(self, property, 0)


class TeamProfile(db.Model):
  tv         = db.IntegerProperty(default=0)
  cash       = db.IntegerProperty(default=0)
  ff         = db.IntegerProperty(default=0)
  rerolls    = db.IntegerProperty(default=0)
  apoths     = db.IntegerProperty(default=0)
  cheers     = db.IntegerProperty(default=0)
  coaches    = db.IntegerProperty(default=0)

  # Glicko rating
  glicko_r   = db.FloatProperty(default=1500.0)
  glicko_RD  = db.FloatProperty(default=350.0)

  # Verification status
  INCONSISTENT_FLAG = 0 # inconsistent data
  INELIGIBLE_FLAG   = 1 # ineligible due to multiple teams of a given race
  PRE_LE_FLAG       = 2 # history incomplete
  status            = db.IntegerProperty(default=0)

  def set_flag(self, flag):
    self.status |= (1 << flag)

  def clear_flag(self, flag):
    self.status &= ~(1 << flag)

  def test_flag(self, flag):
    return bool(self.status & (1 << flag))

  def update(self, team_profile):
    for property in TeamProfile.properties():
      setattr(self, property, getattr(team_profile, property))


class TeamLogo(db.Model):
  box     = db.BlobProperty()
  thumb   = db.BlobProperty()


class Team(TeamStats, TeamProfile):
  # key_name = name
  coach   = db.ReferenceProperty(models.Coach)
  race    = db.ReferenceProperty(Race)
  created = db.DateProperty(auto_now_add=True)
  logo    = db.StringProperty(default="logo_neutre_07.png")
  color   = db.StringProperty(default="#000000")
  retired = db.BooleanProperty(default=False)

  def check_eligibility(self, season):

    if self.test_flag(TeamProfile.INELIGIBLE_FLAG):
      return False

    if not self.coach:
      return True

    key_name = "%s:%s" % (season, self.race.key().name())
    eligibility = models.TeamEligibility.get_by_key_name(
        key_name, parent=self.coach)

    if not eligibility:

      # build the OFL coach -> race map
      ofl_info = urlfetch.fetch(
          "http://www.shalkith.com/bloodbowl/displayCoach.php")
      assert ofl_info.status_code == 200

      race_map = {
          "Dwarf":    "Dwarves",
          "Halfling": "Halflings",
          "Human":    "Humans",
          "Orc":      "Orcs",
          "Pro Elf":  "Pro Elves",
          "Wood Elf": "Wood Elves",
          "Dark Elf": "Dark Elves",
          "High Elf": "High Elves",
          }

      map = {}
      for line in ofl_info.content.splitlines():
        line = line.strip()
        if line:
          coach, race = line.split("\\")
          map[coach] = race_map.get(race, race)

      # see if this coach is currently in the OFL with a team of that race
      if map.get(self.coach.key().name()) == self.race.key().name():
        models.TeamEligibility(
            key_name=key_name,
            parent=self.coach,
            team=None).put()
        return False

      else:
        models.TeamEligibility(
            key_name=key_name,
            parent=self.coach,
            team=self).put()
        return True

    else:
      # if the eligibility has a team associated with it (it relates to the
      # OFTL) and the team is this team, then the team is eligible
      return eligibility.team and eligibility.team.key() == self.key()

  last_active = db.DateProperty()

  # record statistics
  matches    = db.IntegerProperty(default=0)
  wins       = db.IntegerProperty(default=0)
  draws      = db.IntegerProperty(default=0)
  losses     = db.IntegerProperty(default=0)

  # pre bb-oftl record statistics
  pre_wins       = db.IntegerProperty()
  pre_draws      = db.IntegerProperty()
  pre_losses     = db.IntegerProperty()

  # tournament points
  tpts       = db.IntegerProperty(default=0)

  # adjusted win percentage
  awp        = db.FloatProperty(default=0.0)

  # coach preferences
  bio          = db.TextProperty(default="")
  custom_logo  = db.ReferenceProperty(TeamLogo)

  def get_logo_url(self, size="box"):
    if self.custom_logo:
      return 'get_logo?team_key=%s&size=%s' % (self.key(), size)
    else:
      if size == "box":
        return 'images/logos/%s' % self.logo
      else:
        return 'images/logos/%s/%s' % (size, self.logo)
  

  def update(self, team_record):
    super(Team, self).update(team_record)
    self.accumulate(team_record)

    def inc_wins():   self.wins   += 1
    def inc_draws():  self.draws  += 1
    def inc_losses(): self.losses += 1

    self.matches += 1
    attr_map = {
        1:  'wins',
        0:  'draws',
        -1: 'losses',
        }
    attr = attr_map[team_record.result]
    setattr(self, attr, getattr(self, attr) + 1)

    self.compute_awp()
    self.compute_glicko(team_record)

  def recompute(self):
    self.reset()

    # everything that is a read-modify-write update must be reset
    # TODO: this should be part of a reset function
    self.matches = 0
    self.wins = 0
    self.losses = 0
    self.draws = 0
    self.glicko_r = 1500.0
    self.glicko_RD = 350.0
    # tpts should be included here but is not because the system is not
    # designed around it -- tpts is not updated by "update()".
    # I will just have to fix it manually if it needs to be fixed.

    for record in self.teamrecord_set.order('created'):
      self.update(record)

  def compute_awp(self):
    self.awp = max(0.0,
        (self.wins + self.draws/2.0) / self.matches - 
        1 / math.sqrt(self.matches))

  def compute_glicko(self, my_record):
    # get this team info
    my_r  = my_record.glicko_r
    my_RD = my_record.glicko_RD
    my_tv = my_record.tv

    # (regress RD)
    c = 50.0
    my_RD = min(math.sqrt(my_RD**2 + c**2), 350.0)

    # get opponent info
    vs_r  = my_record.opponent_record.glicko_r
    vs_RD = my_record.opponent_record.glicko_RD
    vs_tv = my_record.opponent_record.tv

    # compute variables
    q = 0.0057565
    s = (my_record.result + 1) / 2.0
    g = 1 / (math.sqrt(1 + 3*(q**2)*(vs_RD**2)/(math.pi**2)))

    E = 1 / (1.0 + 10 ** (-g * (
      ((my_r  - vs_r)  / 400.0) +
      # tv adjustment
      ((((my_tv - vs_tv) / float(min(my_tv, vs_tv))) * 1000.0) / 700.0)
      )))

    d2 = 1 / ((q**2) * (g**2) * E*(1-E))
    tmp = 1/(my_RD**2) + 1/d2

    # Compute the new r and RD.  Don't let RD drop below 150.0
    new_r  = my_r + (q / tmp) * (g * (s-E))
    new_RD = max(math.sqrt(1 / tmp), 150.0)

    # debug
    logging.debug("computing glicko: s=%s, g=%s, E=%s, d2=%s, r=%s, RD=%s" % (
      s, g, E, d2, new_r, new_RD))

    # update
    self.glicko_r  = new_r
    self.glicko_RD = new_RD

  def get_box_href(self):
    return '#team?team_key_name=%s' % urllib.quote(self.key().name())

  def get_active_tournament_membership(self):
    for membership in self.tournamentmembership_set:
      if membership.active:
        return membership


