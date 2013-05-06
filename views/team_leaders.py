
from google.appengine.ext import webapp
from operator import attrgetter

import misc, views
from misc.table import Table, Column
from models import TeamLeader, TeamLeaderStanding


class TeamLeaders(views.CachedView):

  def get(self):

    # check for a cached version
    #--------------------------------------------------------------------#

    if self.emit(self.response.out):
      return

    # not cached or evicted from cache; regenerate
    #--------------------------------------------------------------------#

    def logo_getter(standing):
      team = standing.team
      img = "<img src='%s' />" % team.get_logo_url() # FIXME: thumb is broken
      return "<div style='background-color: %(color)s'>%(img)s</div>" % {
          'color': team.color, 'img': img}

    def name_getter(standing):
      team = standing.team
      return "<a class='leader_link' rel='leader_team' href='%s'>%s</a>" % (
          team.get_box_href(), team.key().name())

    leader_info = []
    for leader in TeamLeader.all().order('display_order'):
      query = TeamLeaderStanding.all().ancestor(leader).order('-score').fetch(10)

      leader_table = Table(
          columns = [
            Column(" ",         "Logo",      logo_getter, center=True),
            Column("Team Name", "Team name", name_getter),
            Column("Score",     "Score",     attrgetter("score")),
            ],
          query = query,
          cls = "leader_table",
          )

      def get_left_header(tuple):
        subquery, which = tuple
        return which.capitalize()

      def getter(stat):
        def getter_closure(tuple):
          subquery, which = tuple
          html = []
          for i, standing in enumerate(subquery):
            attr = getattr(standing.team, "%s_%s" % (stat, which))
            html.append("<span class='leader_info leader_info_%s'>%s</span>" % (i+1, attr))
          return "\n".join(html)

        return getter_closure

      def played_getter(tuple):
        subquery, which = tuple
        html = []
        for i, standing in enumerate(subquery):
          attr = getattr(standing.team, "matches")
          html.append("<span class='leader_info leader_info_%s'>%s</span>" % (i+1, attr))
        return "\n".join(html)

      leader_stats_table = Table(
          columns = [
            Column("",   "",                 get_left_header),
            Column("Pl", "Matches played",   played_getter),
            Column("TD", "Touchdowns",       getter("tds")),
            Column("P",  "Pass completions", getter("passes")),
            Column("YP", "Yards passing",    getter("pyards")),
            Column("R",  "Pass receptions",  getter("rec")),
            Column("YR", "Yards rushing",    getter("ryards")),
            Column("K",  "Kills",            getter("kills")),
            Column("C",  "Casualties",       getter("cas")),
            Column("KO", "Knock outs",       getter("ko")),
            Column("T",  "Tackles",          getter("tckl")),
            Column("I",  "Interceptions",    getter("int")),
            ],
          query = ((query, "for"), (query, "against")),
          cls = "fancytable leader_stats_table",
          )

      teams = [s.team for s in query]
      team_names = ["%s<i style='font-weight: normal'>, %s</i>" % (
        s.team.key().name(), s.team.coach.key().name() if s.team.coach else "Unknown")
        for s in query]

      leader_info.append((
        leader, leader_table, leader_stats_table, teams, team_names))

    team_leaders = misc.render('team_leaders.html', locals())
    self.update(team_leaders)

    self.response.out.write(team_leaders)
    
