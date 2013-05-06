
from google.appengine.ext import webapp
from operator import attrgetter

import misc, views
from misc.table import Table, Column
from models import PlayerLeader, PlayerLeaderStanding


class PlayerLeaders(views.CachedView):

  def get(self):

    # check for a cached version
    #--------------------------------------------------------------------#

    if self.emit(self.response.out):
      return

    # not cached or evicted from cache; regenerate
    #--------------------------------------------------------------------#

    def logo_getter(standing):
      team = standing.player.team
      img = ""
      color = '#000000'
      if team:
        img = "<img src='%s' />" % team.get_logo_url() # FIXME: thumb is broken
        color = team.color

      return "<div style='background-color: %(color)s'>%(img)s</div>" % {
          'color': color, 'img': img}

    def name_getter(standing):
      player = standing.player
      return "<a class='leader_link' rel='leader_player' href='%s'>%s</a>" % (
          player.get_box_href(), player.name)

    leader_info = []
    for leader in PlayerLeader.all().order('display_order'):

      query = PlayerLeaderStanding.all().ancestor(leader).order('-score').fetch(10)

      leader_table = Table(
          columns = [
            Column(" ",           "Logo",        logo_getter, center=True),
            Column("Player Name", "Player name", name_getter),
            Column("Score",       "Score",       attrgetter("score")),
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
            try:
              attr = getattr(standing.player, "%s_%s" % (stat, which))
            except AttributeError:
              attr = "-"
            html.append("<span class='leader_info leader_info_%s'>%s</span>" % (i+1, attr))
          return "\n".join(html)

        return getter_closure

      def played_getter(tuple):
        subquery, which = tuple
        html = []
        for i, standing in enumerate(subquery):
          attr = getattr(standing.player, "played")
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

      players = [s.player for s in query]
      player_names = ["%s<i style='font-weight: normal'>, %s</i>" % (
            s.player.name, s.player.team.key().name()) for s in query]

      leader_info.append((
        leader, leader_table, leader_stats_table, players, player_names))

    player_leaders = misc.render('player_leaders.html', locals())
    self.update(player_leaders)

    self.response.out.write(player_leaders)
    
