
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.ext.webapp import template

from models import PlayerLeaderStanding, TeamLeaderStanding
import os.path
import logging
import views


def render(file, map={}):
  return template.render(
      os.path.join(os.path.dirname(__file__), '../templates', file), map)


class AssertLog(list):
  def __init__(self, title):
    self.title = title

  def check(self, left, right, context=None):
    if left != right:
      self.append("%s: %s != %s" % (context, left, right))
      return False
    else:
      return True

  def mail(self):
    if self:
      mail.send_mail(
          sender="verification@bb-oftl.appspotmail.com",
          to="mdekruijf@gmail.com",
          subject="OFTL failure: %s" % self.title,
          body="\n".join(self))
      return True
    else:
      return False


def get_contrasting_monochrome(color):
  # If at least one of the rgb components is greater than 0x80 (128/256) then
  # choose black.  Otherwise, pick white.
  if len([h for h in color[1:6:2] if int(h, 16) > 8]):
    return "#000000"
  else:
    return "#ffffff"


def build_list_for_query(q):
  l = []
  while q.count():
    l.extend(q.fetch(1000))
    q.with_cursor(q.cursor())
  return l


def get_ofl_season_and_week():
  # Get the current OFL season adjusted for post Era 1
  ofl_info = urlfetch.fetch(
      "http://www.shalkith.com/bloodbowl/displayWeek.php")
  assert ofl_info.status_code == 200
  season, week = [int(x) for x in ofl_info.content.strip().split("\\")]
  season -= 3

  return season, week


def retire_team(team):
  team.retired = True
  team.put()

  for player in team.player_set:
    standings = PlayerLeaderStanding.all().filter("player =", player).fetch(100)
    db.delete(standings)

  standings = TeamLeaderStanding.all().filter("team =", team).fetch(100)
  db.delete(standings)

  views.TeamLeaders.clear()
  views.PlayerLeaders.clear()
  views.LeagueStandings.clear()

def unretire_team(team):
  team.retired = False
  team.put()
  views.LeagueStandings.clear()

  

