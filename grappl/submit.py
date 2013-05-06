
from google.appengine.api.labs import taskqueue
from google.appengine.api import mail
from google.appengine.ext import db
import re, logging, random, datetime

from models import *
from grappl.utils import batch_put
import views, misc


def prepare_submit(data, handler=None, localtest=False):

  def read_and_delete(key):
    ret = data.get(key)
    if ret:
      del data[key]
      return ret
    else:
      return ""

  signature  = read_and_delete("signature")
  md5        = read_and_delete("md5")
  disconnect = bool(read_and_delete("disconnect"))
  bblog      = read_and_delete("bblog")

  # get team entities
  team_names = [data["home_name"], data["away_name"]]
  teams = [Team.get_or_insert(name) for name in team_names]

  # this is our match lookup aid
  match_lookup = MatchLookup.get_or_insert(MatchLookup.get_key_name(teams))
  logging.debug("looked up %s" % match_lookup.get_string())

  # There is a race condition here.  We need to refetch the last
  # match inside a transaction before we create the new match.
  def get_or_create_match():
    previous_matches = Match.all().ancestor(
        match_lookup).order("-created").fetch(1)

    if previous_matches:
      last_match = previous_matches[0]
      last_md5   = SubmitData.all().ancestor(last_match).get().md5
    else:
      last_match = None
      last_md5   = None

    # Create the match if any of the following are true:
    #   * their is no prior match on record between these two teams
    #   * the MD5 hashes of this submit and the submit of the last match don't
    #     match up
    if not last_match or last_md5 != md5:
      match = Match(parent = match_lookup, disconnect = disconnect)
      match.put()
      created = True
    else:
      match = last_match
      match.both_submitted = True
      match.put()
      created = False

    submit_data = SubmitData(
        key_name   = signature,
        parent     = match,
        disconnect = disconnect,
        md5        = md5,
        data       = data,
        bblog      = bblog)
    submit_data.put()

    return (match, submit_data, created)

  logging.debug("calling get_or_create_match for %s" % match_lookup.get_string())
  match, submit_data, created = db.run_in_transaction(get_or_create_match)

  if created:
    try:
      # if we created the match, we will initiate processing
      logging.debug("match %s created" % match_lookup.get_string())

      if localtest:
        # dev_appserver has no support for tasks so we do it manually
        process_submit(submit_data, localtest=localtest)
      
      else:
        logging.debug("match %s updated; spawning submit task" %
            match_lookup.get_string())

        taskqueue.add(url="/grappl/tasks/submit", params={
          'submit_data_key_string': submit_data.key(),
          })

    # if we receive an exception delete the match to allow a retry
    except:
      match.delete()
      submit_data.delete()
      raise

  else:
    # check to make sure everything is consistent
    submit_data2 = SubmitData.all().ancestor(
        match).filter("__key__ !=", submit_data.key()).fetch(1)[0]

    my_data    = submit_data.data
    their_data = submit_data2.data

    assert_log = misc.AssertLog(match_lookup.get_string())
    for key in my_data.keys():
      assert_log.check(my_data[key], their_data[key], "my %s" % key)

    for key in their_data.keys():
      assert_log.check(their_data[key], my_data[key], "their %s" % key)

    if assert_log.mail():
      logging.warning("%s verification failed." % match_lookup.get_string())


def process_submit(submit_data, localtest=False):
  """Submit the match.
  
  Ideally we want this whole post to be a transaction, but it would require us
  to lock the whole datastore which is not GAE-like.  We can take advantage of
  memcache to ensure that the updates won't become visible to the web page
  until we're done and we clear out the relevant memcache entries.

  Still, we want to not commit the match record entries (TeamRecord and
  PlayerRecord) until the last possible moment to make the possibility of a
  parallel memcache clear presenting an inconsistent view to the users view
  maximally unlikely."""

  data  = submit_data.data
  match = submit_data.parent()
  match_lookup = match.parent()

  assert_log = misc.AssertLog(match_lookup.get_string())

  # First extract the information into the right categories:
  #   team data,
  #   team record data,
  #   team player data, and
  #   team player record data
  #--------------------------------------------------------------------#

  both_team_data = ({}, {})
  both_players_data = ({}, {})

  both_team_record_data = ({}, {})
  both_player_records_data = ({}, {})

  def str_getter(val): return val # do not use str() in case of unicode
  def int_getter(val): return int(val)
  def bool_getter(val):
    if val:
      return True
    else:
      return False

  # ReferenceProperties
  def position_getter(val): return db.Key.from_path("Position", val)
  def race_getter(val):     return db.Key.from_path("Race", val)

  def skills_getter(val): 
    skills = []
    for skill_name in [s.strip() for s in val.split(",")]:
      if skill_name:
        skills.append(db.Key.from_path("Skill", skill_name))
    return skills

  def injuries_getter(val): 
    injuries = []
    for injury_name in [s.strip() for s in val.split(",")]:
      if injury_name:
        injuries.append(db.Key.from_path("Injury", injury_name))
    return injuries

  team_attr_map = {
      # fixed
      "name":       (True,  str_getter),
      "race":       (True,  race_getter),
      "logo":       (True,  str_getter),
      "color":      (True,  int_getter),

      # profile
      "cash":       (False, int_getter),
      "ff":         (False, int_getter),
      "rerolls":    (False, int_getter),
      "apoths":     (False, int_getter),
      "cheers":     (False, int_getter),
      "coaches":    (False, int_getter),

      # stats
      "result":     (False, int_getter),
      "tv_for":     (False, int_getter),
      "tv_against": (False, int_getter),
      }

  player_attr_map = {
      # fixed
      "number":   (True,  int_getter),
      "bb_id":    (True,  int_getter),
      "position": (True,  position_getter),
      "name":     (True,  str_getter),

      # profile
      "mv":             (False, int_getter),
      "st":             (False, int_getter),
      "ag":             (False, int_getter),
      "av":             (False, int_getter),
      "level":          (False, int_getter),
      "spp":            (False, int_getter),
      "value":          (False, int_getter),
      "skills":         (False, skills_getter),
      "injuries":       (False, injuries_getter),

      # other
      "match_injuries": (False, injuries_getter),

      # stats
      "played":         (False, int_getter),
      "mvps":           (False, int_getter),
      "tds_for":        (False, int_getter),
      "passes_for":     (False, int_getter),
      "pyards_for":     (False, int_getter),
      "rec_for":        (False, int_getter),
      "ryards_for":     (False, int_getter),
      "int_for":        (False, int_getter),
      "int_against":    (False, int_getter),
      "tckl_for":       (False, int_getter),
      "tckl_against":   (False, int_getter),
      "kills_for":      (False, int_getter),
      "kills_against":  (False, int_getter),
      "cas_for":        (False, int_getter),
      "cas_against":    (False, int_getter),
      "ko_for":         (False, int_getter),
      "ko_against":     (False, int_getter),
      "stun_for":       (False, int_getter),
      "stun_against":   (False, int_getter),
      "inj_for":        (False, int_getter),
      "inj_against":    (False, int_getter),
      }

  player_stat_regex = re.compile(
      r"(?P<team_id>\w+)_(?P<player_id>p\d+)_(?P<attr>\w+)")

  for key, value in sorted(data.items()):
    hit = player_stat_regex.match(key)
    if hit:
      # it's a player attribute

      def get_map(team_id, player_id, is_player_data):
        index = (0 if team_id == "home" else 1)
        data  = (both_players_data if is_player_data else
            both_player_records_data)

        return data[index].setdefault(player_id, {})

      team_id, player_id, attr = [str(x) for x in hit.groups()]
      is_player_data, converter = player_attr_map[attr]
      map = get_map(team_id, player_id, is_player_data)

    else:
      # it's a team attribute

      def get_map(is_team_data):
        index = (0 if team_id == "home" else 1)
        data  = (both_team_data if is_team_data else
            both_team_record_data)

        return data[index]

      team_id, attr = [str(x) for x in key.split("_", 1)]
      is_team_data, converter = team_attr_map[attr]
      map = get_map(is_team_data)

    map[attr] = converter(value)


  # Build team aggregate statistics
  #--------------------------------------------------------------------#
  
  for which_team, team_record_data in enumerate(both_team_record_data):
    for attr in sorted(TeamStats.properties()):
      if attr.startswith("tv_"):
        # these are already handled
        continue

      if "for" in attr:
        opp_attr = attr.replace("for", "against")
      else:
        opp_attr = attr.replace("against", "for")

      def compute_aggregate(which_team, attr):
        return sum([v.get(attr, 0) for v in
            both_player_records_data[which_team].values()])

      inputs = ((which_team, attr), (which_team ^ 1, opp_attr))
      sums = [compute_aggregate(*input) for input in inputs]

      if all([s != 0 for s in sums]) and not any(
        [x for x in ("cas_", "kills_", "stun_", "ko_") if x in attr]):
        assert_log.check(sums[0], sums[1], context="aggregate sum for %s" % attr)

      # as a safety, in case we fail we take the maximum of the two
      team_record_data[attr] = max(sums)

  # Now build the actual models
  #--------------------------------------------------------------------#

  both_teams          = []
  both_team_records   = []
  both_players        = ([], [])
  both_player_records = ([], [])

  for team_data in both_team_data:
    # Again, like match, we need to create ("put") the team if it doesn't
    # already exist.  Fortunately this is an idempotent operation.
    team = Team.get_by_key_name(team_data['name'])
    team.race  = team_data['race']
    team.logo  = get_logo(team_data['logo'])
    team.color = get_color(team_data['color'])
    team.last_active = datetime.date.today()
    team.retired = False
    both_teams.append(team)

  for which_team, team_record_data in enumerate(both_team_record_data):
    team = both_teams[which_team]
    team_record_data["parent"]       = match
    team_record_data["key_name"]     = "%s" % which_team
    team_record_data["tv"]           = team_record_data["tv_for"]
    team_record_data["disconnect"]   = submit_data.disconnect
    team_record_data["team"]         = team
    team_record_data["glicko_r"]     = team.glicko_r
    team_record_data["glicko_RD"]    = team.glicko_RD
    team_record_data["status"]       = team.status

    both_team_records.append(TeamRecord(**team_record_data))

  for which_team, players_data in enumerate(both_players_data):
    for player_key, player_data in players_data.items():
      # For the players, just like with the teams and the match, we need to
      # create ("put") the entities first before we can do anything with
      # them.  Just like with the teams, this is an idempotent operation.
      team = both_teams[which_team]
      player_data["team"] = team.key()
      player = Player.create(**player_data)
      both_players[which_team].append(player)

  for which_team, player_records_data in enumerate(
      both_player_records_data):
    for which_player, player_record_data in enumerate(
        player_records_data.values()):

      player_record_data["parent"]   = match
      player_record_data["key_name"] = "%s:%s" % (which_team, which_player)
      player_record_data["player"]   = (
          both_players[which_team][which_player])
      player_record = PlayerRecord(**player_record_data)

      both_player_records[which_team].append(player_record)

  # Prepare to commit
  #--------------------------------------------------------------------#
  put_list = []

  # Update records
  for players, player_records in zip(both_players, both_player_records):
    for player, player_record in zip(players, player_records):
      put_list.append(player)
      put_list.append(player_record)

  for team, team_record in zip(both_teams, both_team_records):
    put_list.append(team)
    put_list.append(team_record)

  # Commit
  #--------------------------------------------------------------------#

  # Batch commit!  This is as close to a transaction as we are going to get.
  logging.debug("preparing to commit phase 1 %s " % match_lookup.get_string())
  batch_put(put_list)

  put_list = []
  # Add some last-minute links to speed things up.  We couldn't do this before
  # because the entities we're linking to didn't exist in the datastore yet
  for which_team, (team, team_record) in enumerate(zip(both_teams, both_team_records)):
    team_record.opponent_record = both_team_records[which_team ^ 1]
    put_list.append(team_record)

    for player_record in both_player_records[which_team]:
      player_record.team_record = team_record
      put_list.append(player_record)

  logging.debug("preparing to commit phase 2 %s " % match_lookup.get_string())
  db.put(put_list)

  # Done!
  logging.debug("submit task for %s terminating successfully" %
      match_lookup.get_string())

  match.processed = True
  match.put()

  assert_log.mail()

  if localtest:
    # dev_appserver has no support for tasks so we do it manually
    process_update(match)
  else:
    logging.debug("spawning update task for %s" % match_lookup.get_string())

    # We do this separately because otherwise we run up against the 30 second
    # limit
    taskqueue.add(url="/grappl/tasks/update", params={
      'match_key_string': match.key(),
      })


def process_update(match):
  match_lookup = match.parent()
  put_list = []

  logging.debug("preparing to update for %s" % match_lookup.get_string())

  assert_log = misc.AssertLog(match_lookup.get_string())
  season, week = misc.get_ofl_season_and_week()

  # Update team information
  #--------------------------------------------------------------------#

  team_records = list(match.get_team_records_query())
  teams = [record.team for record in team_records]
  coach_stats_list = []
  
  for team, team_record in zip(teams, team_records):

    # this check is to make sure we only do this once (for idempotence) in case
    # of a retry
    if team.teamrecord_set.count() > team.matches:
      team.update(team_record)
      coach = team.coach
      if coach:
        coach_stats = CoachStats.all().ancestor(coach).get()
        coach_stats.update(team_record)
        coach_stats_list.append(coach_stats)

      # OFTL eligibility rule checks
      if not team.check_eligibility(season=season):
        team.set_flag(TeamProfile.INELIGIBLE_FLAG)

      # retirement (not by death)
      active_player_count = 0
      player_keys = [pr.player.key() for pr in team_record.playerrecord_set]
      for player in team.player_set:
        if not player.key() in player_keys:
          if player.retired == False:
            player.retired = True
            put_list.append(player)

        if not player.retired:
          active_player_count += 1

      # boost TV for potential loners
      if active_player_count < 11:
        team.tv += (11 - active_player_count) * 50

  # Update player information
  #--------------------------------------------------------------------#

  player_records = list(match.get_player_records_query())
  players = [record.player for record in player_records]

  # Structure to map to the already-updated player team.
  #   We use this map because 'player.team' and the same team indexed in
  #   'teams' do not point to the same object. To avoid conflict we
  #   update the one in 'teams' through the map
  team_map = dict((t.key(), t) for t in teams)

  # Keep track of the number of players that violate the SPP check.  Allow one
  # violation for journeyman hire, which is impossible to track otherwise.
  violation_set = set()
  for player, player_record in zip(players, player_records):
    if not player.team:
      # journeyman / star player
      continue

    if player.matches == 0 and player_record.is_empty():
      # a journeyman/necro/nurgle hire that may have acquired SPP in-game
      continue

    if player.team.key() not in team_map:
      assert player_record.is_empty()
      # Unfortunately BB assigns a journeyman/necro/nurgle hire an arbitrary id
      # that may conflict with an existing OFTL player from a different team.
      # In this case, player.matches != 0. This code is a safety net.
      continue

    # this check is to make sure we only do this once (for idempotence) in case
    # of a retry
    if player.playerrecord_set.count() > player.matches:

      # OFTL rule checks
      if not assert_log.check(player_record.spp, player.spp,
          "%s %s (%s) expected spp" % (
            player.team.key().name(), player.name, player.key().name())):

        # allow one violation for a journeyman hire before setting the
        # inconsistent flag
        if player.spp != 0 or (player.team.key() in violation_set):
          team_map[player.team.key()].set_flag(TeamProfile.INCONSISTENT_FLAG)

        violation_set.add(player.team.key())

      tv_delta = player.update(player_record)
      if tv_delta:
        team_map[player.team.key()].tv += tv_delta

  put_list.extend(coach_stats_list)
  put_list.extend(teams)
  put_list.extend(players)
  batch_put(put_list)

  # Update leader information
  #--------------------------------------------------------------------#

  update_coach_leaders(coach_stats_list)
  update_team_leaders(teams)
  update_player_leaders(players)

  # Update tournament details
  #--------------------------------------------------------------------#

  match_up = match_lookup.tournamentmatchup_set.get() 

  # disqualify team if played match outside of tournament
  for team in teams:
    active_membership = team.get_active_tournament_membership()
    if active_membership and (not match_up or
        match_up.parent().key() != active_membership.parent().key()):

      active_tournament = active_membership.parent()
      if active_tournament.started:
        mail.send_mail(
            sender="verification@bb-oftl.appspotmail.com",
            to="rhaugstrup@gmail.com",
            subject="OFTL rules violation",
            body="%s played outside of %s\n" % (
              team.key().name(), active_tournament.key().name()))
      else:
        # force withdraw
        active_membership.delete()

  # there can only be one tournament for this match
  if match_up:
    tournament = match_up.parent()

    # determine the winner
    if team_records[0].result == 0:
      # decide the winner by a 'coin flip'.  Seed the random number generator by
      # the match key to make it deterministic in case we need to retry
      random.seed(str(match.key()))
      winner_index = random.choice([0, 1])
    else:
      winner_index = 0 if team_records[0].result == 1 else 1

    winner = teams[winner_index]
    winner = winner.tournamentmembership_set.ancestor(tournament).get()

    loser = teams[winner_index ^ 1]
    loser = loser.tournamentmembership_set.ancestor(tournament).get()

    if match_up.advance(winner, loser, match):
      update_team_leaders([winner.team])

    views.TournamentBox.clear(tournament.key())
    views.Tournaments.clear()
    
  # Evict relevant pages from memcache so they are regenerated
  #--------------------------------------------------------------------#

  for team in teams:
    views.TeamBox.clear(team.key())

  for player in players:
    views.PlayerBox.clear(player.key())

  views.RecentMatches.clear()
  views.LeagueStandings.clear()
  views.TeamLeaders.clear()
  views.PlayerLeaders.clear()
  views.CoachLeaders.clear()

  assert_log.mail()
  logging.debug("update successful for %s" % match_lookup.get_string())

def update_coach_leaders(coach_stats_list):
  """Update coach leader standings"""
  put_list = []

  # update leader standings for each Coach
  for leader in CoachLeader.all():
    for coach_stats in coach_stats_list:
        put_list.append(CoachLeaderStanding(
            key_name = coach_stats.parent().key().name(),
            parent = leader,
            coach_stats = coach_stats,
            score = leader.get_score(coach_stats)))

  batch_put(put_list)
  
def update_team_leaders(teams):
  """Update team leader standings"""
  put_list = []

  # update leader standings for each team
  for leader in TeamLeader.all():
    for team in teams:
      if team.matches == 0:
        # pre-registered team
        continue

      put_list.append(TeamLeaderStanding(
          key_name = team.key().name(),
          parent   = leader,
          team     = team,
          score    = leader.get_score(team)))

  batch_put(put_list)


def update_player_leaders(players):
  """Update player leader standings"""
  put_list = []

  # update leader standings for each player
  for leader in PlayerLeader.all():
    for player in players:
      if not player.key().name() or player.played == 0:
        # omit journeymen/star players and players that have not played
        continue

      put_list.append(PlayerLeaderStanding(
          key_name = player.key().name(),
          parent   = leader,
          player   = player,
          score    = leader.get_score(player)))

  batch_put(put_list)


def get_color(num):
  if num>55:
    num=55
	
  color_map = {
      0:  (85 , 209, 255),
      1:  (112, 254, 202),
      2:  (151, 246, 14 ),
      3:  (246, 255, 0  ),
      4:  (241, 186, 138),
      5:  (255, 123, 246),
      6:  (224, 104, 254),
      7:  (223, 229, 229),
      8:  (85 , 169, 255),
      9:  (0  , 255, 252),
      10: (0  , 255, 0  ),
      11: (255, 222, 0  ),
      12: (255, 147, 147),
      13: (255, 85 , 243),
      14: (180, 123, 255),
      15: (192, 191, 191),
      16: (8  , 130, 255),
      17: (3  , 219, 216),
      18: (107, 221, 14 ),
      19: (239, 189, 16 ),
      20: (255, 83 , 83 ),
      21: (246, 0  , 229),
      22: (158, 85 , 255),
      23: (170, 170, 170),
      24: (20 , 60 , 212),
      25: (2  , 168, 166),
      26: (95 , 200, 9  ),
      27: (204, 117, 41 ),
      28: (244, 0  , 0  ),
      29: (158, 0  , 147),
      30: (106, 0  , 246),
      31: (109, 109, 109),
      32: (38 , 77 , 176),
      33: (1  , 108, 107),
      34: (77 , 111, 3  ),
      35: (140, 78 , 29 ),
      36: (180, 0  , 0  ),
      37: (90 , 0  , 84 ),
      38: (68 , 0  , 158),
      39: (62 , 62 , 62 ),
      40: (37 , 61 , 121),
      41: (1  , 78 , 64 ),
      42: (40 , 74 , 7  ),
      43: (90 , 55 , 25 ),
      44: (128, 0  , 0  ),
      45: (54 , 37 , 78 ),
      46: (48 , 4  , 105),
      47: (24 , 24 , 24 ),
      48: (21 , 35 , 69 ),
      49: (1  , 45 , 37 ),
      50: (27 , 50 , 5  ),
      51: (52 , 29 , 9  ),
      52: (74 , 0  , 0  ),
      53: (31 , 21 , 45 ),
      54: (28 , 2  , 60 ),
      55: (14 , 14 , 14 ),
    }

  def get_two_char_hex_string(val):
    s = str(hex(val))[2:4]
    if len(s) == 1:
      s = "0" + s
    return s

  return '#' + "".join(get_two_char_hex_string(val) for val in color_map[num])


def get_logo(logo):
  logo = "logo_%s.png" % logo.lower()
  logos = open("./logos.txt")
  for line in logos:
    if line.strip() == logo:
      break
  else:
    logo = "logo_neutre_07.png"
  logos.close()
  return logo


