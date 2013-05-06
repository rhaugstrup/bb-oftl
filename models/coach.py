from google.appengine.ext import db
from google.appengine.api import urlfetch
import math, logging, urllib, models

class CoachLogo(db.Model):
  box     = db.BlobProperty()
  thumb   = db.BlobProperty()

class Coach(db.Model):
  # key_name = name
  user = db.UserProperty()
  bio = db.TextProperty(default="")
  logo = db.StringProperty(default="logo_neutre_07.png")
  color = db.StringProperty(default="#000000")  
  custom_logo  = db.ReferenceProperty(CoachLogo)
  last_active = db.DateProperty()
  retired = db.BooleanProperty(default=False)
  
  def get_box_href(self):
    return '#coach?coach_key_name=%s' % urllib.quote(self.key().name())

  def get_logo_url(self, size="box"):
    if self.logo == "":
        self.logo = "logo_neutre_07.png"

    if size == "box":
      return 'images/logos/%s' % self.logo
    else:
      return 'images/logos/%s/%s' % (size, self.logo)

# TODO: Implement this code - allows coach to have custom logo
#    if self.custom_logo:
#      return 'get_logo?coach_key=%s&size=%s' % (self.key(), size)
#    else:
#      if size == "box":
#        return 'images/logos/%s' % self.logo
#      else:
#        return 'images/logos/%s/%s' % (size, self.logo)
  


class TeamEligibility(db.Model):
  # key_name = season + ":" + race
  # parent = coach
  team = db.ReferenceProperty()

class CoachStats(db.Model):
#  coach            = db.ReferenceProperty(Coach)
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
 
  matches          = db.IntegerProperty(default=0)
  wins             = db.IntegerProperty(default=0)
  draws            = db.IntegerProperty(default=0)
  losses           = db.IntegerProperty(default=0)

  # pre bb-oftl record statistics
#  pre_wins       = db.IntegerProperty()
#  pre_draws      = db.IntegerProperty()
#  pre_losses     = db.IntegerProperty()

  # tournament points
  tpts       = db.IntegerProperty(default=0)

  # adjusted win percentage
  awp        = db.FloatProperty(default=0.0)

  def addTeam(self, team):
    for property in CoachStats.properties():
      setattr(self, property, getattr(self, property) + getattr(team, property))
    self.compute_awp()
	
	
  def accumulate(self, team_stats):
    for property in CoachStats.properties():
		if "for" in property or "against" in property:
			setattr(self, property, getattr(self, property) + getattr(team_stats, property))

  def reset(self):
    for property in CoachStats.properties():
      if property.startswith("awp"):
        continue
      setattr(self, property, 0)

  def compute_awp(self):
    self.awp = 0.0
    if (self.matches > 1):
      self.awp = max(0.0,
        (self.wins + self.draws/2.0) / self.matches - 
        1 / math.sqrt(self.matches))
		
  def update(self, team_record):
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

