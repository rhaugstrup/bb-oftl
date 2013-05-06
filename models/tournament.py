
from google.appengine.api import images
from google.appengine.api import mail
from google.appengine.ext import db
import urllib, math, random

from models import *

class TournamentMembership(db.Model):
  # id = auto
  # parent = tournament
  active = db.BooleanProperty(default=True)
  team   = db.ReferenceProperty(models.Team)
  seed   = db.IntegerProperty()


class TournamentMatchUp(db.Model):
  # key_name = "{round}:{match_seed}"
  # parent = tournament
  next       = db.SelfReferenceProperty()
  
  # this is set when the match is scheduled but not yet played
  match_lookup = db.ReferenceProperty(models.MatchLookup)

  # these are set after the match is played
  # (if the match is a forfeit, winner is set but match is not)
  match  = db.ReferenceProperty(models.Match)
  winner = db.ReferenceProperty(TournamentMembership)

  def schedule_if_ready(self):
    members = self.tournamentmatchupmembership_set.fetch(2)
    assert len(members) == 2

    if all(m.membership for m in members):
      teams = [m.membership.team for m in members]
      self.match_lookup = models.MatchLookup.get_or_insert(
          models.MatchLookup.get_key_name(teams))
      return True
    else:
      return False

  def email(self):
    members = self.tournamentmatchupmembership_set.fetch(2)
    assert len(members) == 2

    tournament = self.parent()
    teams = [m.membership.team for m in members]
    for i in range(2):
      team = teams[i]
      opponent = teams[i^1]

      mail.send_mail(
          sender="tournaments@bb-oftl.appspotmail.com",
          to=team.coach.user.email(),
          bcc="mdekruijf@gmail.com",
          subject="OFTL tournament '%s' match-up notification!" % tournament.key().name(),
          body="""
Your %s %s tournament match with team %s is now scheduled against %s's %s. 
Please contact %s in the OFL/OFTL forums to arrange your match.
          """ % (
            tournament.key().name(),
            self.get_round_name().lower(),
            team.key().name(),
            opponent.coach.key().name(),
            opponent.key().name(),
            opponent.coach.key().name()))

  def advance(self, winner, loser, match=None):
    tournament = self.parent()

    # update the links
    self.match_lookup = None
    self.match = match
    self.winner = winner
    self.put()

    loser.active = False
    loser.put()

    # advance the winner if this was not the final
    if self.next:
      round, seed = [int(x) for x in self.key().name().split(":")]
      mm = TournamentMatchUpMembership.get_by_key_name(
          "%s:%s" % (round + 1, seed), parent=tournament)

      assert mm.match_up.key() == self.next.key()
      mm.membership = winner
      mm.put()

      # schedule the match
      if self.next.schedule_if_ready():
        self.next.put()
        self.next.email()

    else:
      put_list = [tournament, winner]
      tournament.winning_team = winner.team

      # idempotence check
      if winner.active:
        winner.team.tpts += (
            TournamentMembership.all().ancestor(tournament).count() - 1)
        coach_stats = CoachStats.all().ancestor(winner.team.coach).get()
        coach_stats.tpts += (
            TournamentMembership.all().ancestor(tournament).count() - 1)

        leader = models.CoachLeader.get_by_key_name("Silverware")
        coach_standing = models.CoachLeaderStanding(
            key_name = winner.team.coach.key().name(),
            parent   = leader,
            coach_stats     = coach_stats,
            score    = leader.get_score(coach_stats))

        leader = models.TeamLeader.get_by_key_name("Silverware")
        leader_standing = models.TeamLeaderStanding(
            key_name = winner.team.key().name(),
            parent   = leader,
            team     = winner.team,
            score    = leader.get_score(winner.team))
        put_list.extend([winner.team, leader_standing, coach_stats, coach_standing])

      winner.active = False
      db.put(put_list)


  def get_round_name(self):
    max_seed = 0
    for mm in self.tournamentmatchupmembership_set:
      max_seed = max(max_seed, int(mm.key().name().split(":")[1]))

    round = int(math.log(max_seed, 2))
    map = {
        0: "Final",
        1: "Semi-final",
        2: "Quarter-final",
        3: "Round of 16",
        4: "Round of 32",
        5: "Round of 64",
        }

    return map[round]


class TournamentMatchUpMembership(db.Model):
  # key_name = "{round}:{team_seed}"
  # parent = tournament
  match_up   = db.ReferenceProperty(TournamentMatchUp)
  membership = db.ReferenceProperty(TournamentMembership)


class TournamentPicture(db.Model):
  # key_name = tournament title
  box     = db.BlobProperty()
  cabinet = db.BlobProperty()
  thumb   = db.BlobProperty()

  @classmethod
  def create_from_img(cls, key_name, pic):
    box     = db.Blob(images.resize(pic, 600, 300))
    cabinet = db.Blob(images.resize(pic, 80, 40))
    thumb   = db.Blob(images.resize(pic, 32, 16))
    return cls(key_name=key_name, box=box, cabinet=cabinet, thumb=thumb)


class Tournament(db.Model):
  # key_name = title
  created   = db.DateTimeProperty(auto_now_add=True)
  owner     = db.ReferenceProperty(models.Coach)

  background = db.TextProperty()
  pic        = db.ReferenceProperty(TournamentPicture)

  started      = db.BooleanProperty(default=False)
  winning_team = db.ReferenceProperty(models.Team)

  min_tv    = db.IntegerProperty()
  max_tv    = db.IntegerProperty()
  min_ma    = db.IntegerProperty()
  max_ma    = db.IntegerProperty()

  max_enrollment = db.IntegerProperty()
  seed_by        = db.StringProperty(choices=('Random', 'TV', 'AWP', 'Rating', 'Custom'))
  races_allowed  = db.ListProperty(db.Key)

  def get_box_href(self):
    return '#tournament?tournament_key_name=%s' % urllib.quote(self.key().name())

  def schedule(self):
    assert not self.started, "Tournament already started?!"

    # cache the members of the tournament in a list
    members = list(TournamentMembership.all().ancestor(self))

    # order members by seed
    if self.seed_by == "Custom":
      members.sort(key = lambda m: m.seed)

      for i, member in enumerate(members):
        assert member.seed == i

    else:
      if self.seed_by == "Random":
        random.shuffle(members)
      else:
        seed_attr = self.seed_by.lower()
        if self.seed_by == "Rating":
          seed_attr = "glicko_r"

        members.sort(
            key = lambda m: getattr(m.team, seed_attr),
            reverse=True)

      for i, member in enumerate(members):
        member.seed = i
        member.put()

    # create the match ups for each round
    num_teams  = len(members)
    num_rounds = int(math.ceil(math.log(num_teams, 2)))
    
    # update tournament
    self.started = True
    self.final = db.Key.from_path(
        "Tournament", self.key().name(),
        "TournamentMatchUp", "%s:0" % (num_rounds - 1))
    self.put()

    # iterate over the rounds in order from wildcards to finals
    scheduled_seeds = set()

    for round in range(num_rounds):
      matches_in_round    = 2**(num_rounds - 1 - round)

      def get_next_match_up(seed):
        if round == num_rounds - 1:
          return None
        else:
          if seed < matches_in_round / 2:
            next_seed = seed
          else:
            next_seed = matches_in_round - 1 - seed

          return db.Key.from_path(
              "Tournament", self.key().name(),
              "TournamentMatchUp", "%s:%s" % (round + 1, next_seed))

      # create the match ups for this round and schedule the teams if they are
      # not already scheduled in a previous round
      for seed in range(matches_in_round):

        high_seed = seed
        low_seed  = 2*matches_in_round - 1 - seed
        if low_seed >= num_teams:
          # then we are in the wildcard round and this match doesn't exist
          continue

        match_up = TournamentMatchUp(
            key_name     = "%s:%s" % (round, seed),
            parent       = self,
            next         = get_next_match_up(seed))
        match_up.put()

        for team_seed in (high_seed, low_seed):
          mm = TournamentMatchUpMembership(
              key_name   = "%s:%s" % (round, team_seed),
              parent     = self,
              match_up   = match_up,
              seed       = team_seed)
          if not team_seed in scheduled_seeds:
            scheduled_seeds.add(team_seed)
            mm.membership = members[team_seed]

          mm.put()

        if match_up.schedule_if_ready():
          match_up.put()
          match_up.email()


