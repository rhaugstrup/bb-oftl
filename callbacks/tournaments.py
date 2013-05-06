
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp

import views, misc
from models import Coach, Team
from models import Tournament, TournamentMembership, TournamentMatchUp
from models import TournamentMatchUpMembership, TournamentPicture


class GetTrophy(webapp.RequestHandler):
  def get(self):
    tournament = Tournament.get(self.request.get("tournament_key"))
    if tournament.pic:
      self.response.headers['Content-Type'] = "image/png"
      self.response.out.write(getattr(tournament.pic, self.request.get("size")))
    else:
      self.error(404)


class Create(webapp.RequestHandler):
  def post(self):
    tournament_name  = self.request.get("tournament_name")
    if Tournament.get_by_key_name(tournament_name):
      # TODO error: already exists
      return

    max_enrollment   = int(self.request.get("max_enrollment"))
    assert not (max_enrollment < 4 or max_enrollment > 64)

    background       = self.request.get("background")
    seed_by          = self.request.get("seed_by")
    coach            = Coach.get_by_key_name(self.request.get("coach_key_name"))
    min_tv           = self.request.get("min_tv")
    max_tv           = self.request.get("max_tv")
    min_ma           = self.request.get("min_ma")
    max_ma           = self.request.get("max_ma")

    # compute race restrictions
    race_restriction = self.request.get("race_restriction")
    if race_restriction:
      races_allowed = self.request.get_all("races_allowed")
      races_allowed = [
          db.Key.from_path("Race", race_name) for race_name in races_allowed]
    else:
      races_allowed = []

    tournament = Tournament(
        key_name       = tournament_name,
        owner          = coach,
        background     = background,
        max_enrollment = max_enrollment,
        seed_by        = seed_by,
        races_allowed  = races_allowed)

    def format_tv(tv):
      tv = (tv / 10) * 10
      return max(0, min(3500, tv))

    if min_tv:
      tournament.min_tv = int(min_tv)
    if max_tv:
      tournament.max_tv = int(max_tv)

    if min_ma:
      tournament.min_ma = int(min_ma)
    if max_ma:
      tournament.max_ma = int(max_ma)

    trophy_pic = self.request.get("trophy_pic")
    if trophy_pic:
      pic = TournamentPicture.create_from_img(tournament_name, trophy_pic)
      pic.put()
      tournament.pic = pic

    tournament.put()
    views.Tournaments.clear()

    # I need to give a response or I get an error. Nobody on the internet seems
    # to know why.  See https://github.com/malsup/form/issues#issue/22.
    self.response.out.write("OK") 


class Withdraw(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    coach = Coach.all().filter("user =", user).get()

    tournament = Tournament.get(self.request.get("tournament_key"))
    memberships = [m for m in TournamentMembership.all().ancestor(tournament) if
        m.team.coach.key() == coach.key()]

    membership = memberships[0]
    membership.delete()

    views.Tournaments.clear()


class ForceWithdraw(webapp.RequestHandler):
  def post(self):
    membership = TournamentMembership.get(self.request.get("membership_key"))
    membership.delete()

    views.Tournaments.clear()


class Enroll(webapp.RequestHandler):
  def post(self):
    tournament = Tournament.get(self.request.get("tournament_key"))
    team       = Team.get(self.request.get("team_key"))

    member_count = TournamentMembership.all().ancestor(tournament).count()

    if member_count < tournament.max_enrollment:
      TournamentMembership(parent=tournament, team=team, active=True).put()
      #Unretire team if retired.
      if team.retired:
        misc.unretire_team(team)
        
      if (member_count + 1 == tournament.max_enrollment and
          tournament.seed_by != "Custom"):
        tournament.schedule()


    views.Tournaments.clear()


class GetSeeds(webapp.RequestHandler):
  def get(self):
    tournament = Tournament.get(self.request.get("key"))
    member_count = TournamentMembership.all().ancestor(tournament).count()

    html = ["<input type='hidden' name='tournament_key' value='%s' />" % tournament.key()]
    html.append("<p>Provide each team with a unique seed ranging from 1 to %s:</p>"
        % member_count)
    for member in TournamentMembership.all().ancestor(tournament):
      html.append("%s: <input type='text' name='seed_%s'><br />" % (
        member.team.key().name(), member.key()))

    self.response.out.write("\n".join(html))


class SeedAndStart(webapp.RequestHandler):
  def post(self):
    tournament = Tournament.get(self.request.get("tournament_key"))
    member_count = TournamentMembership.all().ancestor(tournament).count()

    for arg in self.request.arguments():
      if arg.startswith("seed_"):
        member_key = arg.split("_")[1]
        member = TournamentMembership.get(member_key)

        seed = int(self.request.get(arg)) - 1
        assert seed >= 0 and seed < member_count
        member.seed = seed
        member.put()

    tournament.schedule()
    views.Tournaments.clear()


class Start(webapp.RequestHandler):
  def post(self):
    tournament = Tournament.get(self.request.get("tournament_key"))
    tournament.schedule()
    views.Tournaments.clear()


class Cancel(webapp.RequestHandler):
  def post(self):
    tournament_key = db.Key(self.request.get("tournament_key"))

    db.delete(TournamentMembership.all(keys_only=True).ancestor(tournament_key))
    db.delete(TournamentMatchUp.all(keys_only=True).ancestor(tournament_key))
    db.delete(TournamentMatchUpMembership.all(keys_only=True).ancestor(tournament_key))
    db.delete(tournament_key)
    views.Tournaments.clear()


class Forfeit(webapp.RequestHandler):
  def post(self):
    forfeit_mm = TournamentMatchUpMembership.get(self.request.get("mm_key"))

    match_up = forfeit_mm.match_up
    for match_up_mm in match_up.tournamentmatchupmembership_set:
      if match_up_mm.key() != forfeit_mm.key():
        winner_mm = match_up_mm
        break

    match_up.advance(winner_mm.membership, forfeit_mm.membership)

    tournament = match_up.parent()
    views.TournamentBox.clear(tournament.key())
    views.Tournaments.clear()


