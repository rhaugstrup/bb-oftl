
from google.appengine.ext import webapp
from operator import attrgetter
import math, datetime

import models
import misc, views
from misc.table import Table, Column


class LeagueStandings(views.CachedView):

  def get(self):

    # check for a cached version
    #--------------------------------------------------------------------#

    if self.emit(self.response.out):
      return

    # not cached or evicted from cache; regenerate
    #--------------------------------------------------------------------#

    season, week = misc.get_ofl_season_and_week()
    ofl_week = (season - 1) * 16 + week

    def name_getter(team):
      return "<a rel='team' href='%s'>%s</a>" % (
          team.get_box_href(), team.key().name())

    def race_getter(team):
      return "<img title='%s' src='%s' />" % (
          team.race.key().name(), team.race.get_image_src(thumb=True))

    def coach_getter(team):
      if team.coach:
        return "<a rel='coach' href='%s'>%s</a>" % (
          team.coach.get_box_href(),team.coach.key().name())
      else:
        return "<i>Unknown</i>"

    def awp_getter(team):
      return "%0.3f" % team.awp

    def glicko_getter(team):
      return "%4.0f" % team.glicko_r

    def status_getter(team):
      html = []

      matches = team.matches
      if team.pre_wins != None:
        matches += team.pre_wins + team.pre_draws + team.pre_losses

      #if (team.status or matches > ofl_week or not team.coach):
      #  html.append("<span class='red_text'>OFL Ineligible</span>")

      if not team.coach:
          html.append("<span class='orange_text'>(Unclaimed!)</span>")

      elif team.test_flag(models.TeamProfile.INCONSISTENT_FLAG):
          html.append("<span class='red_text'>(Inconsistent Data!)</span>")

      #  elif team.test_flag(models.TeamProfile.INELIGIBLE_FLAG):
      #    html.append("<span class='orange_text'>(Exceeds Quota)</b>")

      elif team.test_flag(models.TeamProfile.PRE_LE_FLAG):
          html.append("<span class='yellow_text'>(Incomplete History)</span>")

       # else:
       #  html.append("<span class='orange_text'>(Ahead of OFL Schedule)</b>")

      else:
          html.append("<span class='green_text'>Consistent Data</span>")

      if team.pre_wins != None:
          html.append(
              "<span class='yellow_text'>(Pre-LE history validated: %sW-%sD-%sL)</span>"
              % (team.pre_wins, team.pre_draws, team.pre_losses))

      return " ".join(html)


    #def get_ave_getter(attr):
    #  def ave_getter(team):
    #    return "%.1f" % (float(getattr(team, attr)) / team.matches)
    #  return ave_getter

    tables = {}
    #Getting rid of retired table
    #for label in ("active", "retired"):
    #Taking for loop out, and removing an indent from tables line
    label = "active"
    tables[label] = Table(
          columns = [
            # profile
            Column(" ",         "Race",               race_getter, center=True),
            Column("Team Name", "Team name",          name_getter),
            Column("Coach",     "Coach",              coach_getter),
            Column("TV",        "Team value (approximate)",
              attrgetter("tv"), divider=True),

            # record
            Column("Pl",        "Matches played",     attrgetter("matches")),
            Column("W",         "Matches won",        attrgetter("wins")),
            Column("D",         "Matches drawn",      attrgetter("draws")),
            Column("L",         "Matches lost",       attrgetter("losses"),
              divider=True),

            # rankings
            Column("AWP",       "Adjusted win percentage", awp_getter),
            Column("TPts",      "Tournament Points",       attrgetter("tpts")),
            Column("Rating",    "Glicko Rating",           glicko_getter,
              divider=True),

            Column("Status & Eligibility",
              "OFTL/OFL Status and/or Eligibility",    status_getter),
            ## touchdowns
            #Column("TD+",       "Touchdowns for",     attrgetter("tds_for")),
            #Column("TD-",       "Touchdowns against", attrgetter("tds_against")),
            #Column("<span class='over'>TD+</span>",  "Average touchdowns for",
            #  get_ave_getter("tds_for")),
            #Column("<span class='over'>TD-</span>",  "Average touchdowns against",
            #  get_ave_getter("tds_against")),

            ## casualties
            #Column("C+",        "Casualties for",     attrgetter("cas_for")),
            #Column("C-",        "Casualties against", attrgetter("cas_against")),
            #Column("<span class='over'>C+</span>",  "Average casualties for",
            #  get_ave_getter("cas_for")),
            #Column("<span class='over'>C-</span>",  "Average casualties against",
            #  get_ave_getter("cas_against")),
            ],
          query = models.Team.all().filter("retired =", label == "retired").filter(
            "matches >", 0).order("-matches"),
          id = "team-standings-table",
          cls = "tablesorter",
          )

    # render and update
    #--------------------------------------------------------------------#

    league_standings = misc.render('league_standings.html', locals())
    self.update(league_standings)

    self.response.out.write(league_standings)

