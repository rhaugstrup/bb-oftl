
from google.appengine.ext import db
from google.appengine.ext import webapp
from operator import attrgetter

from models import Team, CoachStats, Coach, TeamRecord
import misc, views
from misc.table import Table, Column


class CoachBox(views.CachedView):

  def get(self):

    # check for a cached version
    #--------------------------------------------------------------------#

    coach_key = db.Key.from_path("Coach", self.request.get("coach_key_name"))
    if self.emit(self.response.out, coach_key):
      return

    # not cached or evicted from cache; regenerate
    #--------------------------------------------------------------------#

    coach = Coach.get(coach_key)
    if not coach:
      return

    coach_stats = CoachStats.all().ancestor(coach).get()
    # win/draw/loss bars and banner text color
    #--------------------------------------------------------------------#

    longest_bar_length = max(coach_stats.wins, coach_stats.draws, coach_stats.losses)
    banner_text_color = misc.get_contrasting_monochrome(coach.color)

    # team_table
    #--------------------------------------------------------------------#

    def name_getter(team):
      return "<a rel='team' href='%s'>%s</a>" % (
          team.get_box_href(), team.key().name())

    def race_getter(team):
      return "<img title='%s' src='%s' />" % (
          team.race.key().name(), team.race.get_image_src(thumb=True))

    def awp_getter(team):
      return "%0.3f" % team.awp

    def glicko_getter(team):
      return "%4.0f" % team.glicko_r
    
    teams = query = Team.all().filter("coach =", coach).filter("matches >", 0).order("-matches")
    team_table = Table(
          columns = [
            # profile
            Column(" ",         "Race",               race_getter, center=True),
            Column("Team Name", "Team name",          name_getter),
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
          query = teams,
          id = "%s-team-table" % coach.key(),
          cls = "tablesorter",
          )


    # coach_stat_table
    #--------------------------------------------------------------------#

    def get_left_header(tuple):
      coach_stats, which = tuple
      return which.capitalize()

    def getter(stat):
      def getter_closure(tuple):
        coach_stats, which = tuple
        attr = getattr(coach_stats, "%s_%s" % (stat, which))
        return (
            ("<span class='tot_stat'>%d</span>" % attr) +
            ("<span class='ave_stat'>%.1f</span>" % (attr / float(coach_stats.matches))))

      return getter_closure

    stat_table = Table(
        columns = [
          Column("<span class='link' id='%s-show-averages-toggle'></span>" %
            coach.key(), "", get_left_header),
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
        query = ((coach_stats, "for"), (coach_stats, "against")),
        cls = "fancytable stats",
        )

    # render and update (TODO: move to bottom after implementing bottom code)
    #--------------------------------------------------------------------#

    coach_box = misc.render('coach_box.html', locals())
    self.update(coach_box, coach_key)

    self.response.out.write(coach_box)
'''
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
    for team in teams:
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
'''
#    active_member = team.get_active_tournament_membership()
#    active_tournament = active_member.parent() if active_member else None



