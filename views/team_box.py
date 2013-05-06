
from google.appengine.ext import db
from google.appengine.ext import webapp
from operator import attrgetter

from models import Team
import misc, views
from misc.table import Table, Column


class TeamBox(views.CachedView):

  def get(self):

    # check for a cached version
    #--------------------------------------------------------------------#

    team_key = db.Key.from_path("Team", self.request.get("team_key_name"))
    if self.emit(self.response.out, team_key):
      return

    # not cached or evicted from cache; regenerate
    #--------------------------------------------------------------------#

    team = Team.get(team_key)
    if not team:
      return

    # win/draw/loss bars and banner text color
    #--------------------------------------------------------------------#

    longest_bar_length = max(team.wins, team.draws, team.losses)
    banner_text_color = misc.get_contrasting_monochrome(team.color)

    # player_table
    #--------------------------------------------------------------------#

    def position_getter(player):
      return player.position.key().name()

    def name_getter(player):
      if player.played:
        return "<a rel='team_players' href='%s'>%s</a>" % (
            player.get_box_href(), player.name)
      else:
        return "<b>" + player.name + "</b>"

    def mng_getter(player):
      if player.missing_next_game:
        return "<img src='images/logos/thumb/logo_neutre_10.png' />"
      else:
        return ""

    player_table = Table(
        columns = [
          Column("#",           "Player number",      attrgetter("number"),
            center=True),
          Column("MNG",         "Missing next game",  mng_getter,
            center=True),
          Column("Player",      "Player name",        name_getter),
          Column("Position",    "Player position",    position_getter,
            divider=True),
          Column("MV",          "Movement allowance", attrgetter("mv")),
          Column("ST",          "Strength",           attrgetter("st")),
          Column("AG",          "Agility",            attrgetter("ag")),
          Column("AV",          "Armor value",        attrgetter("av"),
            divider=True),
          Column("SPP",         "Star player points", attrgetter("spp")),
          Column("Level",       "Level",              attrgetter("level"),
            divider=True),
          Column("Pl",          "Matches played",     attrgetter("played")),
          Column("MVP",         "Most Valuable Player awards", attrgetter("mvps")),
          Column("TD",          "Touchdowns",         attrgetter("tds_for")),
          Column("P",           "Pass completions",   attrgetter("passes_for")),
          Column("YP",          "Yards passing",      attrgetter("pyards_for")),
          Column("R",           "Pass receptions",    attrgetter("rec_for")),
          Column("YR",          "Yards rushing",      attrgetter("ryards_for")),
          Column("K",           "Kills",              attrgetter("kills_for")),
          Column("C",           "Casualties",         attrgetter("cas_for")),
          Column("KO",          "Knock outs",         attrgetter("ko_for")),
          Column("S",           "Stuns",              attrgetter("stun_for")),
          Column("T",           "Tackles",            attrgetter("tckl_for")),
          Column("I",           "Interceptions",      attrgetter("int_for"),
            divider=True),
          Column("Value",       "Player value",       attrgetter("value")),
          ],
        query = team.player_set.filter("retired =", False),
        id = "%s-player-table" % team.key(),
        cls = "tablesorter",
        )

    # stat_table
    #--------------------------------------------------------------------#

    def get_left_header(tuple):
      team, which = tuple
      return which.capitalize()

    def getter(stat):
      def getter_closure(tuple):
        team, which = tuple
        attr = getattr(team, "%s_%s" % (stat, which))
        return (
            ("<span class='tot_stat'>%d</span>" % attr) +
            ("<span class='ave_stat'>%.1f</span>" % (attr / float(team.matches))))

      return getter_closure

    stat_table = Table(
        columns = [
          Column("<span class='link' id='%s-show-averages-toggle'></span>" %
            team.key(), "", get_left_header),
          Column("TD", "Touchdowns",       getter("tds")),
          Column("P",  "Pass completions", getter("passes")),
          Column("YP", "Yards passing",    getter("pyards")),
          Column("R",  "Pass receptions",  getter("rec")),
          Column("YR", "Yards rushing",    getter("ryards")),
          Column("K",  "Kills",            getter("kills")),
          Column("C",  "Casualties",       getter("cas")),
          Column("KO", "Knock outs",       getter("ko")),
          Column("S",  "Stuns",            getter("stun")),
          Column("T",  "Tackles",          getter("tckl")),
          Column("I",  "Interceptions",    getter("int")),
          ],
        query = ((team, "for"), (team, "against")),
        cls = "fancytable stats",
        )

    # match_tables
    #--------------------------------------------------------------------#

    def name_getter(record):
      if record.team.key() == team.key():
        return team.key().name()
      else:
        return "<a rel='team_opponents' href='%s'>%s</a>" % (
            record.team.get_box_href(), record.team.key().name())

    def race_getter(record):
      return "<img src='%s' />" % record.team.race.get_image_src(thumb=True)

    def link_getter(record):
      return """
      <a rel='team_matches' href='%s'>
      <span class="go_to_arrow" title='Go to match page'>&rarr;</span></a>""" % (
          record.get_match().get_box_href())

    def glicko_getter(record):
      return "%4.0f" % record.glicko_r

    match_columns = [
        Column(" ",         "Race",             race_getter,
          center=True),
        Column("Team",      "Team name",        name_getter),
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
        Column("", "", link_getter, center=True, rowspan=2)
        ]

    # get matches from match_records and sort in order of most recent
    matches = sorted(
        [record.get_match() for record in team.teamrecord_set],
        key=lambda m: m.created, reverse=True)

    match_tables = []
    for match in matches:
      # sort with this team's match record first
      match_records = sorted(
          match.get_team_records_query(),
          key=lambda mr: mr.team.key() == team.key(),
          reverse=True)

      result_map = {
          1  : "WIN!",
          0  : "DRAW",
          -1 : "LOSS"}

      title = "(%s) <b>%s-%s %s</b> vs. %s" % (
          match.created.date(),
          match_records[0].tds_for,
          match_records[1].tds_for,
          result_map[match_records[0].result],
          match_records[1].team.key().name())

      if match.disconnect:
        title += " (Disconnect/Forfeit)"

      match_table = Table(
          columns = match_columns,
          query = match_records,
          cls = "tablesorter match_stats",
          title = title)

      match_tables.append((match.get_box_href(), match_table))

    active_member = team.get_active_tournament_membership()
    active_tournament = active_member.parent() if active_member else None

    # render and update
    #--------------------------------------------------------------------#

    team_box = misc.render('team_box.html', locals())
    self.update(team_box, team_key)

    self.response.out.write(team_box)

