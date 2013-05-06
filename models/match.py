
from google.appengine.ext import db

import properties
from models import *
  

class MatchLookup(db.Model):
  # id = teamA vs. teamB

  @staticmethod
  def get_key_name(teams):
    return " vs. ".join(sorted([t.key().name() for t in teams]))

  def get_string(self):
    return self.key().name()

  def get_teams(self):
    return [Team.get_by_key_name(x) for x in self.key().name().split(" vs. ")]


class SubmitData(db.Model):
  # key_name = signature
  # parent = match
  uploaded   = db.DateTimeProperty(auto_now_add=True)
  data       = properties.DictProperty()
  md5        = db.StringProperty()
  disconnect = db.BooleanProperty(default=False)
  bblog      = db.TextProperty(default=None)


class TeamRecord(TeamStats, TeamProfile):
  # LEGACY: id = auto
  # key_name = {which_team}
  # parent = match
  created         = db.DateTimeProperty(auto_now_add=True)
  match           = db.ReferenceProperty() # LEGACY
  team            = db.ReferenceProperty(Team)
  opponent_record = db.SelfReferenceProperty()

  # -1 = loss, 0 = draw, 1 = win
  result     = db.IntegerProperty()
  disconnect = db.BooleanProperty(default=False)

  submit_data = db.ReferenceProperty(SubmitData)

  def get_match(self):
    if self.match:
      return self.match
    else:
      return self.parent()


class PlayerRecord(PlayerStats, PlayerProfile):
  # LEGACY: id = auto
  # key_name = {which_team}:{which_player}
  # parent = match
  created        = db.DateTimeProperty(auto_now_add=True)
  match          = db.ReferenceProperty()  # LEGACY
  player         = db.ReferenceProperty(Player)
  team_record    = db.ReferenceProperty(TeamRecord)
  match_injuries = db.ListProperty(db.Key)

  def get_match(self):
    if self.match:
      return self.match
    else:
      return self.parent()


class Match(db.Model):
  # id = auto
  # parent = match lookup
  created        = db.DateTimeProperty(auto_now_add=True)
  both_submitted = db.BooleanProperty(default=False)
  processed      = db.BooleanProperty(default=False)
  disconnect     = db.BooleanProperty(default=False)

  def get_team_records_query(self):
    ideal_query = TeamRecord.all().ancestor(self)
    if ideal_query.count():
      return ideal_query
    else:
      return self.teamrecord_set 

  def get_player_records_query(self):
    ideal_query = PlayerRecord.all().ancestor(self)
    if ideal_query.count():
      return ideal_query
    else:
      return self.playerrecord_set

  def get_box_href(self):
    return '#match?match_key=%s' % self.key()



