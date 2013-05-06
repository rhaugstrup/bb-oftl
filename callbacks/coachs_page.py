
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp

from models import *
import views, misc


# Handlers for various callbacks
# ------------------------------

class Register(webapp.RequestHandler):
  def post(self):
    coach_name = self.request.get("coach_name")
    user = users.get_current_user()

    assert Coach.get_by_key_name(coach_name) == None

    if user:
      Coach(key_name = coach_name, user = user).put()


class GetLogo(webapp.RequestHandler):
  def get(self):
    team = Team.get(self.request.get("team_key"))
    if team.custom_logo:
      self.response.headers['Content-Type'] = "image/png"
      self.response.out.write(getattr(team.custom_logo, self.request.get("size")))
    else:
      self.error(404)


class ChangeLogo(webapp.RequestHandler):
  def post(self):
    team = Team.get(self.request.get("team_key"))
    if team.custom_logo:
      team.custom_logo.delete()
      team.custom_logo = None
      team.put()

    team_logo = self.request.get("logo")
    box    = db.Blob(images.resize(team_logo, 128, 128))
    thumb  = db.Blob(images.resize(team_logo, 20, 20))

    logo = TeamLogo(key_name=team.key().name(), box=box, thumb=thumb)
    logo.put()

    team.custom_logo = logo
    team.put()

    views.RecentMatches.clear()
    views.TeamBox.clear(team.key())
    views.TeamLeaders.clear()

    for player in team.player_set:
      views.PlayerBox.clear(player.key())

    # I need to give a response or I get an error. Nobody on the internet seems
    # to know why.  See https://github.com/malsup/form/issues#issue/22.
    self.response.out.write("OK") 


class GetPic(webapp.RequestHandler):
  def get(self):
    player = Player.get(self.request.get("player_key"))
    if player.pic:
      self.response.headers['Content-Type'] = "image/png"
      self.response.out.write(getattr(player.pic, self.request.get("size")))
    else:
      self.error(404)


class ChangePic(webapp.RequestHandler):
  def post(self):
    player = Player.get(self.request.get("player_key"))
    if player.pic:
      player.pic.delete()
      player.pic = None
      player.put()

    player_pic = self.request.get("pic")
    box    = db.Blob(images.resize(player_pic, 380, 532))
    leader = db.Blob(images.resize(player_pic, 80, 112))
    thumb  = db.Blob(images.resize(player_pic, 20, 28))

    pic = PlayerPicture(key_name=player.key().name(),
        box=box, leader=leader, thumb=thumb)
    pic.put()

    player.pic = pic
    player.put()

    views.PlayerBox.clear(player.key())
    views.PlayerLeaders.clear()

    # I need to give a response or I get an error. Nobody on the internet seems
    # to know why.  See https://github.com/malsup/form/issues#issue/22.
    self.response.out.write("OK") 


class GetBio(webapp.RequestHandler):
  def get(self):
    team_or_player = db.get(self.request.get("key"))
    self.response.out.write(
        team_or_player.bio if team_or_player.bio else "")


class ChangeBio(webapp.RequestHandler):
  def post(self):
    key = self.request.get("key")
    team_or_player = db.get(key)
    team_or_player.bio = self.request.get("bio")
    team_or_player.put()

    if db.Key(key).kind() == "Team":
      views.TeamBox.clear(team_or_player.key())
    else:
      views.PlayerBox.clear(team_or_player.key())


class ClaimTeam(webapp.RequestHandler):
  def post(self):
    team = Team.get_by_key_name(self.request.get("team_name"))

    user = users.get_current_user()

    if team and user:
      coach = Coach.all().filter("user =", user).get()
      team.coach = coach  
      team.put()  
    
    coach_stats = CoachStats.all().ancestor(coach).get()
    if not coach_stats:    #Coach doesn't have stats yet.
      coach_stats = CoachStats(parent=coach)
    
    for record in team.teamrecord_set.order('created'):
      coach_stats.update(record)
    coach_stats.put()
  
    for leader in CoachLeader.all():
      CoachLeaderStanding(
        key_name = coach_stats.parent().key().name(),
        parent   = leader,
        coach_stats     = coach_stats,
        score    = leader.get_score(coach_stats)).put()

    views.CoachLeaders.clear()
    views.RecentMatches.clear()
    views.LeagueStandings.clear()
    views.TeamBox.clear(team.key())

    # OFL eligibility rule checks
    season, week = misc.get_ofl_season_and_week()
    if not team.check_eligibility(season=season):
      team.set_flag(TeamProfile.INELIGIBLE_FLAG)
      team.put()


class PreRegister(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()

    key_name = self.request.get("team_name")
    race = db.Key.from_path("Race", self.request.get("team_race"))
    tv = int(self.request.get("team_tv"))
    coach = Coach.all().filter("user =", user).get()

    Team.get_or_insert(key_name, race=race, tv=tv, coach=coach)


class Retire(webapp.RequestHandler):
  def post(self):
    team = Team.get(self.request.get("team_key"))

    if not team.matches:
      team.delete()

    else:
      team.retired = not team.retired
      if not team.retired:
        misc.retire_team(team)
      team.put()

    views.LeagueStandings.clear()

class ClearForOFL(webapp.RequestHandler):
  def post(self):
    team = Team.get(self.request.get("team_key"))
    team.pre_wins = int(self.request.get("wins"))
    team.pre_draws = int(self.request.get("draws"))
    team.pre_losses = int(self.request.get("losses"))

    team.clear_flag(TeamProfile.PRE_LE_FLAG)
    team.clear_flag(TeamProfile.INCONSISTENT_FLAG)
    team.put()
    views.LeagueStandings.clear()

