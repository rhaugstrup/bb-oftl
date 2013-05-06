
from google.appengine.ext import db
from google.appengine.ext import webapp
from operator import attrgetter

from models import Player

import misc, views
from misc.table import Table, Column

class PlayerBox(views.CachedView):

  def get(self):

    # check for a cached version
    #--------------------------------------------------------------------#

    player_key = db.Key.from_path("Player", self.request.get("player_key_name"))
    if self.emit(self.response.out, player_key):
      return

    # not cached or evicted from cache; regenerate
    #--------------------------------------------------------------------#

    player = Player.get(player_key)
    if not player:
      return

    # player card
    #--------------------------------------------------------------------#

    banner_text_color = misc.get_contrasting_monochrome(player.team.color)

    attr_table = Table(
        columns = [
          Column("MV", "Movement Allowance", attrgetter("mv")),
          Column("ST", "Strength",           attrgetter("st")),
          Column("AG", "Agility",            attrgetter("ag")),
          Column("AV", "Armor Value",        attrgetter("av")),
          ],
        query = (player,),
        cls = "attr",
        )

    injuries = []
    for injury_key in player.injuries:
      injury = db.get(injury_key)
      if injury.key().name() == "Dead":
        injuries.append("DEAD")
      elif injury.permanent:
        injuries.append("%s (%s)" % (injury.key().name(), injury.effect))
    injuries = ", ".join(x for x in injuries)

    skills = [k.name() for k in player.skills]
    if player.level_up_pending:
      skills.append("<i>Pending Level-Up</i>")
    skills = ", ".join(skills)

    # stat_table
    #--------------------------------------------------------------------#

    def get_left_header(tuple):
      player, which = tuple
      return which.capitalize()

    def getter(stat):
      def getter_closure(tuple):
        player, which = tuple
        try:
          attr = getattr(player, "%s_%s" % (stat, which))
          ave_attr = attr if player.played == 0 else attr / float(player.played)
          return """<div class='tot_stat'>%d</div>
                    <div class='ave_stat'>%.1f</div>""" % (
                        attr, ave_attr)
        except AttributeError:
          return "-"

      return getter_closure

    stat_table = Table(
        columns = [
          Column("<span class='link' id='%s-show-averages-toggle'></span>" %
            player.key(), "", get_left_header),
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
        query = ((player, "for"), (player, "against")),
        cls = "fancytable stats",
        )

    # match_table
    #--------------------------------------------------------------------#

    def name_getter(record):
      opponent = record.team_record.opponent_record.team
      return "<a rel='player_opponents' href='%s'>%s</a>" % (
          opponent.get_box_href(), opponent.key().name())

    def race_getter(record):
      opponent = record.team_record.opponent_record.team
      return "<img src='%s' />" % opponent.race.get_image_src(thumb=True)

    def date_getter(record):
      return record.get_match().created.date()

    def link_getter(record):
      return """
      <a rel='player_matches' href='%s'>
      <span class='go_to_arrow' title='Go to match page'>&rarr;</span></a>""" % (
          record.get_match().get_box_href())

    match_table = Table(
        columns = [
          Column("Date",      "Match date",            date_getter),
          Column("Opponent",  "Opponent name",         name_getter),
          Column(" ",         "Race",                  race_getter,
            center=True),
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
          Column("", "", link_getter, center=True)
          ],
        query = player.playerrecord_set.filter("played =", 1),
        cls = "tablesorter match_stats",
        )

    # render and update
    #--------------------------------------------------------------------#

    player_box = misc.render('player_box.html', locals())
    self.update(player_box, player_key)

    self.response.out.write(player_box)

