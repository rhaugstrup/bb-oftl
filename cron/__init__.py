
from google.appengine.ext import db
from google.appengine.ext import webapp
import datetime, logging

import misc
from models import Team

class RetireTeams(webapp.RequestHandler):

  def get(self):
    logging.debug("checking team retirement....")

    sixteen_weeks_ago = datetime.date.today() - datetime.timedelta(weeks=16)

    for team in Team.all().filter("retired =", False):
      if not team.last_active:
        assert team.matches == 0
        continue

      if team.last_active < sixteen_weeks_ago:
        logging.debug("retiring %s" % team.key().name())
        misc.retire_team(team)

