
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from operator import attrgetter

import misc, views
from models import Coach, Race
from models import Tournament, TournamentMembership, TournamentMatchUp
from misc.table import Table, Column

class Tournaments(views.CachedView):

  def get(self):

    # check for a cached version
    #--------------------------------------------------------------------#

    if self.emit(self.response.out):
      return

    # not cached or evicted from cache; regenerate
    #--------------------------------------------------------------------#

    user = users.get_current_user()
    coach = None
    if user:
      coach = Coach.all().filter("user =", user).get()

    def trophy_getter(tournament):
      if tournament.pic:
        return "<img src='get_trophy?size=thumb&tournament_key=%s' />" % tournament.key()
      return ""

    def name_getter(tournament):
      return "<a rel='tournaments' href='%s'>%s</a>" % (
          tournament.get_box_href(), tournament.key().name())

    def date_getter(tournament):
      return tournament.created.date()

    def organizer_getter(tournament):
      return tournament.owner.key().name()

    def enrollment_getter(tournament):
      return "%s/%s" % (
        TournamentMembership.all().ancestor(tournament).count(),
        tournament.max_enrollment)

    def final_enrollment_getter(tournament):
      return TournamentMembership.all().ancestor(tournament).count()

    def winner_getter(tournament):
      return "<a rel='winners' href='%s'>%s</a> (%s)" % (
          tournament.winning_team.get_box_href(),
          tournament.winning_team.key().name(),
          tournament.winning_team.coach.key().name())

    def tv_getter(tournament):
      if tournament.min_tv and tournament.max_tv:
        return "%s - %s" % (tournament.min_tv, tournament.max_tv)
      elif tournament.min_tv:
        return "&ge; %s" % tournament.min_tv
      elif tournament.max_tv:
        return "&le; %s" % tournament.max_tv
      else:
        return "Any"

    def ma_getter(tournament):
      if tournament.min_ma != None and tournament.max_ma != None:
        return "%s - %s" % (tournament.min_ma, tournament.max_ma)
      elif tournament.min_ma != None:
        return "&ge; %s" % tournament.min_ma
      elif tournament.max_ma != None:
        return "&le; %s" % tournament.max_ma
      else:
        return "Any"
      
    def races_getter(tournament):
      if tournament.races_allowed:
        return "Restricted"
      else:
        return "Any"

    tournaments = {}
    for tournament in Tournament.all():
      if tournament.winning_team:
        tournaments.setdefault("Completed", []).append(tournament)
      elif tournament.started:
        tournaments.setdefault("In Progress", []).append(tournament)
      else:
        tournaments.setdefault("Open", []).append(tournament)

    tables = [
        ("Open", Table(
          columns = [
            Column("",           "Trophy Image",    trophy_getter,
              center=True),
            Column("Name",       "Tournament name",      name_getter),
            Column("Created",    "Creation date",        date_getter),
            Column("Organizer",  "Tournament organizer", organizer_getter),
            Column("Enrolled",   "Enrollment count",     enrollment_getter),
            Column("TV",         "TV range",             tv_getter),
            Column("Matches Played", "Matches played range", ma_getter),
            Column("Races",      "Races allowed",        races_getter),
            Column("Seed By",    "Teams are seeded by",  attrgetter("seed_by")),
            ],
          query = tournaments.get("Open", []),
          cls = "tablesorter tournaments_table",
          )),

        ("In Progress", Table(
          columns = [
            Column("",           "Trophy Image",    trophy_getter,
              center=True),
            Column("Name",       "Tournament name",      name_getter),
            Column("Created",    "Creation date",        date_getter),
            Column("Organizer",  "Tournament organizer", organizer_getter),
            Column("Enrolled",   "Final enrollment count",     final_enrollment_getter),
            Column("TV",         "TV range",             tv_getter),
            Column("Races",      "Races allowed",        races_getter),
            ],
          query = tournaments.get("In Progress", []),
          cls = "tablesorter tournaments_table",
          )),

        ("Completed", Table(
          columns = [
            Column("",           "Trophy Image",    trophy_getter,
              center=True),
            Column("Name",       "Tournament name",      name_getter),
            Column("Created",    "Creation date",        date_getter),
            Column("Organizer",  "Tournament organizer", organizer_getter),
            Column("Winner",     "Tournament winner",    winner_getter),
            Column("Enrolled",   "Final enrollment count",     final_enrollment_getter),
            Column("TV",         "TV range",             tv_getter),
            Column("Races",      "Races allowed",        races_getter),
            ],
          query = tournaments.get("Completed", []),
          cls = "tablesorter tournaments_table",
          ))]

    # render and update 
    #--------------------------------------------------------------------#

    tournaments = misc.render('tournaments.html', locals())
    self.update(tournaments)
    self.response.out.write(tournaments)


