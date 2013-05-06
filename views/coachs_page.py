
from google.appengine.api import users
from google.appengine.ext import webapp
from operator import attrgetter

from models import *

import misc, views
from misc.table import Table, Column


def get_coach_player_tables(coach):

  def name_getter(player):
    return "<a rel='coach_players' href='%s'>%s</a>" % (
        player.get_box_href(), player.name)

  def position_getter(player):
    return player.position.key().name()

  def pic_getter(player):
    img = ""
    if player.pic:
      img = "<img src='get_pic?size=thumb&player_key=%s' />" % player.key()

    return """<div class='link change_pic'
              id='player_pic_%(player_key)s'>%(img)s</div>""" % {
        'img': img,
        'player_key': player.key()}

  def bio_getter(player):
    if player.bio and player.bio.strip():
      if len(player.bio) > 40:
        bio = "%s..." % player.bio[:40]
      else:
        bio = player.bio
    else:
      bio = "<i>None</i>"

    return "<span class='link change_bio' id='player_bio_%(player_key)s'>%(bio)s</span>" % {
        'bio': bio,
        'player_key': player.key()}

  def retired_getter(player):
    if player.retired:
      return "Yes"
    else:
      return "No"

  coach_player_tables = []
  for team in Team.all().filter("coach =", coach).filter(
      "matches >", 0).filter("retired =", False):
    table = Table(
        columns = [
          Column("#",           "Player number",    attrgetter("number"),
            center=True),
          Column("Player Name", "Player name",      name_getter),
          Column("Position",    "Player position",  position_getter),
          Column("Retired",     "Retired",          retired_getter),
          Column("Level",       "Level",            attrgetter("level")),
          Column("Picture",     "Player picture",   pic_getter),
          Column("Biography",   "Player bio",       bio_getter),
          ],
        query = team.player_set,
        id = "coach_player_table_for_team_%s" % team.key(),
        cls = "tablesorter coach_player_table",
        title = team.key().name(),
        )

    coach_player_tables.append(table)

  return coach_player_tables


def get_coach_team_table(coach):

  def name_getter(team):
    if team.matches:
      return "<a rel='coach_teams' href='%s'>%s</a>" % (
          team.get_box_href(), team.key().name())
    else: 
      return "<b>%s</b> <i>(pre-registered)</i>" % (team.key().name())

  def logo_getter(team):
    img = ""
    if team.custom_logo:
      img = "<img src='get_logo?size=thumb&team_key=%s' />" % team.key()

    return """<div class='link change_logo'
              id='team_logo_%(team_key)s'>%(img)s</div>""" % {
        'img': img,
        'team_key': team.key()}

  def bio_getter(team):
    if team.bio and team.bio.strip():
      if len(team.bio) > 40:
        bio = "%s..." % team.bio[:40]
      else:
        bio = team.bio
    else:
      bio = "<i>None</i>"

    return "<span class='link change_bio' id='team_bio_%(team_key)s'>%(bio)s</span>" % {
        'bio': bio,
        'team_key': team.key()}

  def retire_getter(team):
    if team.get_active_tournament_membership():
      return "<i>Active in tournament</i>"
	#else:
	#  return "Available"
	
    html = ['<form class="ajax_form" action="/retire_team" method="post">']
    html.append('<input type="hidden" name="team_key" value="%s" />' % (
      team.key()))

    #if not team.matches:
      #html.append('<input type="submit" value="Delete"/>')

    #elif team.retired:
      #html.append('<input type="submit" value="Unretire"/>')

    #else:
      #html.append('<input type="submit" value="Retire"/>')

    html.append('</form>')
    return "\n".join(html)

  return Table(
      columns = [
        Column("TV",          "Team value (approximate)", attrgetter("tv")),
        Column("Team Name",   "Team name",          name_getter),
        Column("Custom Logo", "Custom team logo",   logo_getter),
        Column("Biography",   "Team bio",           bio_getter),
        Column("Status",      "Tournament Activity",        retire_getter),
        ],
      query = Team.all().filter("retired =", False).filter("coach =", coach),
      cls = "tablesorter coach_team_table",
      )

def get_coach_tournament_table(coach):

  my_tournaments = []
  for tournament in Tournament.all().filter("owner =", coach):
    if tournament.winning_team:
      # this tournament has already completed
      continue
    my_tournaments.append(tournament)

  def trophy_getter(tournament):
    if tournament.pic:
      return "<img src='get_trophy?size=thumb&tournament_key=%s' />" % tournament.key()
    return ""

  def name_getter(tournament):
    return "<a rel='coach_tournaments' href='%s'>%s</a>" % (
        tournament.get_box_href(), tournament.key().name())

  def status_getter(tournament):
    if tournament.winning_team:
      team = tournament.winning_team
      return "Winner: <a rel='winning_teams' href='%s'>%s</a>" % (
          team.get_box_href(), team.key().name())
    if tournament.started:
      return "In progress"
    return "Open"

  def forfeit_getter(tournament):
    enrolled = TournamentMembership.all().ancestor(tournament)
    pending_matches = list(TournamentMatchUp.all().ancestor(tournament).filter(
          "match_lookup !=", None))

    if pending_matches:
      html = ['<form class="ajax_form" action="/forfeit_team" method="post">']
      html.append('<select name="mm_key">')
      for match_up in pending_matches:
        for mm in match_up.tournamentmatchupmembership_set.order("__key__"):
          html.append('<option value="%s">%s</option>' % (
            mm.key(), mm.membership.team.key().name()))
      html.append('</select>')
      html.append('<input type="submit" value="Forfeits!"/>')
      html.append('</form>')
      return "\n".join(html)
    elif enrolled:
      html = ['<form class="ajax_form" action="/force_withdraw" method="post">']
      html.append('<select name="membership_key">')
      for member in enrolled:
        html.append('<option value="%s">%s</option>' % (
          member.key(), member.team.key().name()))
      html.append('</select>')
      html.append('<input type="submit" value="Withdraws!"/>')
      html.append('</form>')
      return "\n".join(html)
    else:
      return "<i>No teams enrolled</i>"

  def start_getter(tournament):
    if tournament.started:
      return '<i>Tournament already started</i>'
    elif TournamentMembership.all().ancestor(tournament).count() < 4:
      return '<i>Insufficient enrollment</i>'
    else:
      if tournament.seed_by == "Custom":
        return """<input class='change_seeding' type='submit' value='Seed and Start!'
          id='tournament_seeding_%s' /""" % tournament.key()
      else:
        html = ['<form class="ajax_form" action="/start_tournament" method="post">']
        html.append('<input type="hidden" name="tournament_key" value="%s" />' % (
          tournament.key()))
        html.append('<input type="submit" value="Start!"/>')
        html.append('</form>')
        return "\n".join(html)

  def cancel_getter(tournament):
    if not tournament.started:
      html = ['<form class="ajax_form" action="/cancel_tournament" method="post">']
      html.append('<input type="hidden" name="tournament_key" value="%s" />' % (
        tournament.key()))
      html.append('<input type="submit" value="Cancel"/>')
      html.append('</form>')
      return "\n".join(html)
    else:
      return '<i>Tournament already started</i>'

  if my_tournaments:
    return Table(
        columns = [
          Column("",             "Trophy Image",    trophy_getter, center=True),
          Column("Name",         "Tournament name", name_getter),
          Column("Status",       "Status",               status_getter),
          Column("Forfeit/Withdraw Team",
            "Choose a team to withdraw from this tournament", forfeit_getter),
          Column("Start Early",  "Start the tournament early", start_getter),
          Column("Cancel",       "Cancel the tournament before it starts", cancel_getter),
          ],
        query = my_tournaments,
        cls = "tablesorter coach_tournaments_table",
        )
  else:
    return None
	

class CoachsPage(webapp.RequestHandler):

  def get(self):

    user = users.get_current_user()
    if user:
      log_out_url = users.create_logout_url("/")
      coach = Coach.all().filter("user =", user).get()
      if coach:
        unclaimed_teams = Team.all().filter("retired =", False).filter("coach =", None)
        coach_team_table = get_coach_team_table(coach)
        coach_player_tables = get_coach_player_tables(coach)
        coach_tournament_table = get_coach_tournament_table(coach)

        ofl_admin = coach.key().name() in [
            "masher", "Thul", "Isryion", "bob152", "Styxx" , "mardaed"]

        if ofl_admin:
          ineligible_teams = [
              team for team in Team.all().filter("status >", 0)
              if (team.test_flag(TeamProfile.PRE_LE_FLAG) or
                  team.test_flag(TeamProfile.INCONSISTENT_FLAG))]

    else:
      log_in_url = users.create_login_url("/")

    races = Race.all()

    self.response.out.write(
        misc.render('coachs_page.html', locals()))


