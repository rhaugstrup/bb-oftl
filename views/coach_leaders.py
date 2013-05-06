
from google.appengine.ext import webapp
from operator import attrgetter

import misc, views
from misc.table import Table, Column
from models import CoachLeader, CoachLeaderStanding


class CoachLeaders(views.CachedView):

  def get(self):

    # check for a cached version
    #--------------------------------------------------------------------#

    if self.emit(self.response.out):
      return

    # not cached or evicted from cache; regenerate
    #--------------------------------------------------------------------#

    def logo_getter(standing):
      coach = standing.coach_stats.parent()
      img = "<img src='%s' />" % coach.get_logo_url() # FIXME: thumb is broken
      return "<div style='background-color: %(color)s'>%(img)s</div>" % {
          'color': coach.color, 'img': img}

    def name_getter(standing):
      coach = standing.coach_stats.parent()
      return "<a class='leader_link' rel='leader_coach' href='%s'>%s</a>" % (
          coach.get_box_href(),coach.key().name())


    leader_info = []
    for leader in CoachLeader.all().order('display_order'):
      query = CoachLeaderStanding.all().ancestor(leader).order('-score').fetch(10)

      leader_table = Table(
          columns = [
            Column(" ",         "Logo",      logo_getter, center=True),
            Column("Coach Name", "Coach name", name_getter),
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
            attr = getattr(standing.coach_stats, "%s_%s" % (stat, which))
            html.append("<span class='leader_info leader_info_%s'>%s</span>" % (i+1, attr))
          return "\n".join(html)

        return getter_closure

      def played_getter(tuple):
        subquery, which = tuple
        html = []
        for i, standing in enumerate(subquery):
          attr = getattr(standing.coach_stats, "matches")
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

      teams = [s.coach_stats for s in query]
      team_names = ["%s<i style='font-weight: normal'>, %s - %s - %s</i>" % (
        s.coach_stats.parent().key().name() if s.coach_stats.parent() else "Unknown", s.coach_stats.wins, s.coach_stats.draws, s.coach_stats.losses)
        for s in query]

      leader_info.append((
        leader, leader_table, leader_stats_table, teams, team_names))

    coach_leaders = misc.render('coach_leaders.html', locals())
    self.update(coach_leaders)

    self.response.out.write(coach_leaders)
    
