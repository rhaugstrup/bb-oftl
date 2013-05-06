
from google.appengine.ext import db
from google.appengine.ext import webapp
from operator import attrgetter

import misc, views
from misc.table import Table, Column
from misc.match_data import MatchData

from models import Match, Injury

class MatchBox(views.CachedView):

  def get(self):

    # check for a cached version
    #--------------------------------------------------------------------#

    match_key = db.Key(self.request.get("match_key"))
    if self.emit(self.response.out, match_key):
      return

    # not cached or evicted from cache; regenerate
    #--------------------------------------------------------------------#

    match = Match.get(match_key)
    if not match:
      return

    home_record, away_record = match.get_team_records_query().fetch(2)
    match_data = MatchData(match)

    # team_match_table
    #--------------------------------------------------------------------#

    def team_name_getter(record):
      return "<a rel='match_teams' href='%s'>%s</a>" % (
          record.team.get_box_href(), record.team.key().name())

    def race_getter(record):
      return "<img src='%s' />" % record.team.race.get_image_src(thumb=True)

    def glicko_getter(record):
      return "%4.0f" % record.glicko_r

    team_match_table = Table(
        columns = [
          Column(" ",         "Race",             race_getter,
            center=True),
          Column("Team",      "Team name",        team_name_getter),
          Column("Rating",    "Team rating",      glicko_getter),
          Column("TV",        "Team value",       attrgetter("tv_for")),
          Column("TD",        "Touchdowns",       attrgetter("tds_for")),
          Column("P",         "Pass completions", attrgetter("passes_for")),
          Column("YP",        "Yards passing",    attrgetter("pyards_for")),
          Column("R",         "Pass receptions",  attrgetter("rec_for")),
          Column("YR",        "Yards rushing",    attrgetter("ryards_for")),
          Column("K",         "Kills",            attrgetter("kills_for")),
          Column("C",         "Casualties",       attrgetter("cas_for")),
          Column("KO",        "Knock outs",       attrgetter("ko_for")),
          Column("S",         "Stuns",            attrgetter("stun_for")),
          Column("T",         "Tackles",          attrgetter("tckl_for")),
          Column("I",         "Interceptions",    attrgetter("int_for")),
          ],
        query = match.get_team_records_query(),
        cls = "tablesorter team_match_table",
        )

    # player_match_tables
    #--------------------------------------------------------------------#

    def number_getter(record):
      return record.player.number

    def player_name_getter(record):
      return record.player.get_box_anchor("match_players")

    def position_getter(record):
      position = record.player.position
      if position.starplayer:
        return "<b>Star Player</b>"
      else:
        return position.key().name()

    player_records = match.get_player_records_query().filter("played =", 1)
    team_player_records = {}
    for record in player_records:
      team_player_records.setdefault(
          record.team_record.team.key().name(), []).append(record)

    player_match_tables = []
    for team_name, record_set in team_player_records.items():
      table = Table(
          columns = [
            Column("#",         "Player number",         number_getter,
              center=True),
            Column("Player",    "Player name",           player_name_getter),
            Column("Position",  "Player position",       position_getter),
            Column("TD",        "Touchdowns",            attrgetter("tds_for")),
            Column("MVP",       "Most Valuable Player Awards", attrgetter("mvps")),
            Column("P",         "Pass completions",      attrgetter("passes_for")),
            Column("YP",        "Yards passing",         attrgetter("pyards_for")),
            Column("R",         "Pass receptions",       attrgetter("rec_for")),
            Column("YR",        "Yards rushing",         attrgetter("ryards_for")),
            Column("K+",        "Kills for",             attrgetter("kills_for")),
            Column("C+",        "Casualties for",        attrgetter("cas_for")),
            Column("KO+",       "Knock outs for",        attrgetter("ko_for")),
            Column("S+",        "Stuns for",             attrgetter("stun_for")),
            Column("T+",        "Tackles for",           attrgetter("tckl_for")),
            Column("I+",        "Interceptions for",     attrgetter("int_for")),
            Column("K-",        "Kills against",         attrgetter("kills_against")),
            Column("C-",        "Casualties against",    attrgetter("cas_against")),
            Column("KO-",       "Knock outs against",    attrgetter("ko_against")),
            Column("S-",        "Stuns against",         attrgetter("stun_against")),
            Column("T-",        "Tackles against",       attrgetter("tckl_against")),
            Column("I-",        "Interceptions against", attrgetter("int_against")),
            ],
          query = record_set,
          cls = "tablesorter player_match_table",
          )

      player_match_tables.append((team_name, table))

    # injury_table
    #--------------------------------------------------------------------#

    def team_name_getter(record):
      return record.team_record.team.key().name()

    def injury_name_getter(record):
      for injury_key in record.match_injuries:
        injury = Injury.get(injury_key)
        if injury.permanent:
          break
      return injury.key().name()

    def injury_effect_getter(record):
      for injury_key in record.match_injuries:
        injury = Injury.get(injury_key)
        if injury.permanent:
          break
      return injury.effect

    injured_player_records = [r for r in player_records if r.match_injuries]

    if injured_player_records:
      injury_table = Table(
          columns = [
            Column("#",      "Player number", number_getter,
              center=True),
            Column("Team",   "Team name",     team_name_getter),
            Column("Player", "Player name",   player_name_getter),
            Column("Position",    "Player position",    position_getter),
            Column("SPP",    "Star player points", attrgetter("spp")),
            Column("Level",  "Level",              attrgetter("level")),
            Column("Injury", "Injury name",   injury_name_getter),
            Column("Effect", "Injury effect", injury_effect_getter),
            ],
          query = injured_player_records,
          cls = "tablesorter injury_table",
          )
    else: 
      injury_table = None


    # render and update 
    #--------------------------------------------------------------------#

    match_box = misc.render('match_box.html', locals())
    self.update(match_box, match_key)

    self.response.out.write(match_box)

