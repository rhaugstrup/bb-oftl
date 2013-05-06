
from google.appengine.ext import db
import logging

import models
import views

# utilities
#--------------------------------------------------------------------#

def batch_put(put_list, chunk_size=500):

  put_elements = len(put_list)
  logging.debug("putting %s elements" % (put_elements))
  for i in range(put_elements / chunk_size):
    j=i+1
    put_chunk = put_list[i*chunk_size:j*chunk_size]
    try:
      db.put(put_chunk)
    except Exception, e:
      logging.warning("Handling exception: %s" % e)
      batch_put(put_chunk, max(chunk_size/10, 1))
  else:
    if put_elements % chunk_size != 0:
      i = put_elements / chunk_size
      db.put(put_list[i*chunk_size:])

import grappl.submit

# shortcuts
#--------------------------------------------------------------------#

def get_last_match(count=0):
  return models.Match.all().order('-created').fetch(1, offset=count)[0]

def delete_player(p, delete_pic=True):
  for pls in p.playerleaderstanding_set:
    pls.delete()
  if p.pic and delete_pic:
    p.pic.delete()
  p.delete()

def delete_team(t):
  for tls in t.teamleaderstanding_set:
    tls.delete()
  t.delete()


# repairs
#--------------------------------------------------------------------#

def mark_team_pre_le(team_name):
  t = models.Team.get_by_key_name(team_name)
  t.clear_flag(models.TeamProfile.INCONSISTENT_FLAG)
  t.set_flag(models.TeamProfile.PRE_LE_FLAG)
  t.put()

  views.LeagueStandings.clear()


def fix_LE_team_transfer(team_name):

  team = models.Team.get_by_key_name(team_name)

  player_map = {}
  for p1 in team.player_set.fetch(100):
    p2 = player_map.get(p1.name)

    if p2:
      keep = p1
      no_keep = p2
      if int(p2.key().name()) > int(p1.key().name()):
        keep = p2
        no_keep = p1

      print "keeping", keep.key().name(), "and not", no_keep.key().name()

      for record in no_keep.playerrecord_set:
        record.player = keep
        record.put()

      if no_keep.pic:
        keep.pic = no_keep.pic
      keep.recompute()
      keep.put()
      delete_player(no_keep, delete_pic=False)

      grappl.submit.update_player_leaders([keep])

    else:
      player_map[p1.name] = p1

  views.TeamBox.clear(team.key())


def matchup_switch_winner(mu):
  mms = mu.tournamentmatchupmembership_set.fetch(2)
  for mm in mms:
    if mm.membership.key() == mu.winner.key():
      loser = mm.membership
    else:
      winner = mm.membership

  mu.advance(winner, loser, mu.match)

  views.TournamentBox.clear(mu.parent().key())
  views.Tournaments.clear()


def fix_preregistration(wrong_name, right_name):

  wrong_team = models.Team.get_by_key_name(wrong_name)
  right_team = models.Team.get_by_key_name(right_name)
  right_team.coach = wrong_team.coach
  right_team.put()
                                     
  # fix the tournament membership
  membership = wrong_team.tournamentmembership_set.get()
  membership.team = right_team
  membership.put()

  # get a handle on the match
  match = right_team.teamrecord_set.get().parent()
  submit_data = models.SubmitData.all().ancestor(match).fetch(1)[0]

  # get a handle on the match lookups
  right_match_lookup = match.parent()

  wrong_teams = []
  for team in right_match_lookup.get_teams():
    if team.key() == right_team.key():
      wrong_teams.append(wrong_team)
    else:
      wrong_teams.append(team)
  wrong_match_lookup = models.MatchLookup.get_or_insert(
      models.MatchLookup.get_key_name(wrong_teams))

  # fix the tournament match up
  match_up = wrong_match_lookup.tournamentmatchup_set.get() 
  match_up.match_lookup = right_match_lookup
  match_up.put()

  # determine the winner
  tournament = membership.parent()
  match = submit_data.parent()

  team_records = match.get_team_records_query().fetch(2)
  if team_records[0].result == 0:
    # decide the winner by a 'coin flip'.  Seed the random number generator by
    # the match key to make it deterministic in case we need to retry
    random.seed(str(match.key()))
    winner_index = random.choice([0, 1])
  else:
    winner_index = 0 if team_records[0].result == 1 else 1

  winner = team_records[winner_index].team
  winner = winner.tournamentmembership_set.ancestor(tournament).get()

  loser = team_records[winner_index ^ 1].team
  loser = loser.tournamentmembership_set.ancestor(tournament).get()

  assert winner and loser
  if match_up.advance(winner, loser, match):
    update_team_leaders([winner.team])

  views.TournamentBox.clear(tournament.key())
  views.Tournaments.clear()
  views.RecentMatches.clear()
    
  # delete the old team
  delete_team(wrong_team)


def undo_match(match):

  match.processed = False
  match.put()

  players = []
  for player_record in match.get_player_records_query():
    players.append(player_record.player)
    player_record.delete()

  teams = []
  for team_record in match.get_team_records_query():
    teams.append(team_record.team)
    team_record.delete()

  for player in players:
    player.recompute()
    player.put()

  for team in teams:
    team.recompute()
    team.put()

  grappl.submit.update_player_leaders(players)
  grappl.submit.update_team_leaders(teams)


