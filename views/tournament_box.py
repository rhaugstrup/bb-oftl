
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
import logging

from models import Coach, Team, Race
from models import Tournament, TournamentMembership, TournamentMatchUp
import misc, views


class TournamentBox(views.CachedView):

  def get(self):

    # check for a cached version
    #--------------------------------------------------------------------#

    tournament = Tournament.get_by_key_name(self.request.get(
      "tournament_key_name"))

    if tournament.started:
      if self.emit(self.response.out, tournament.key()):
        return

    # not cached or evicted from cache; regenerate
    #--------------------------------------------------------------------#

    teams = [m.team for m in TournamentMembership.all().ancestor(tournament)]

    races_allowed = []
    for race_key in tournament.races_allowed:
      races_allowed.append(Race.get(race_key))

    if not tournament.started:
      user = users.get_current_user()
      coach = None
      if user:
        coach = Coach.all().filter("user =", user).get()

      signed_up = False
      if coach:
        signed_up = any(coach.key() == t.coach.key() for t in teams)

      if coach and not signed_up:
        eligible_teams = []
        for team in coach.team_set:
          #if team.retired:
          #  # retired teams cannot enter
          #  continue

          if ((tournament.min_tv and team.tv < tournament.min_tv) or
              (tournament.max_tv and team.tv > tournament.max_tv)):
            # ineligible TV
            continue

          if ((tournament.min_ma != None and team.matches < tournament.min_ma) or
              (tournament.max_ma != None and team.matches > tournament.max_ma)):
            # ineligible matches played
            continue

          if tournament.races_allowed and not any(
              team.race.key() == race for race in tournament.races_allowed):
            # ineligible race
            continue

          if team.get_active_tournament_membership():
            # already active in other tournament
            continue

          eligible_teams.append(team)

    else:

      match_ups = []
      def inorder_insert(match_up, child=None):
        predecessors = match_up.tournamentmatchup_set.order('__key__').fetch(2)

        def get_predecessors(preds):
          if len(preds) == 2:
            return preds
          elif len(preds) == 1:
            return None, preds[0]
          else:
            return None, None

        high, low = get_predecessors(predecessors)

        # visit high
        if high:
          inorder_insert(high, 0)

        # action on self
        match_ups.append((match_up, child))

        # visit low
        if low:
          inorder_insert(low, 1)

      final = TournamentMatchUp.all().ancestor(tournament).filter('next =', None).get()
      inorder_insert(final)
      round, seed = [int(x) for x in final.key().name().split(":")]
      
      # pixel settings
      width_unit = 530 / round
      match_width = 200

      # compute data for each match_up
      match_up_data = []
      for match_up, child in match_ups:
        round, seed = [int(x) for x in match_up.key().name().split(":")]
        position_left = round * width_unit

        team_data = []
        for i, mm in enumerate(
            match_up.tournamentmatchupmembership_set.order("__key__")):

          data = {}
          data["name"]  = "_" * 25
          data["seed"]  = ""
          data["score"] = ""

          if mm.membership:
            team = mm.membership.team
            if team.matches:
              data["name"] = "<a rel='tournament_teams' href='%s'>%s</a>" % (
                  team.get_box_href(), team.key().name())
            else:
              data["name"] = "<b title='%s'>%s</b>" % (
                  team.coach.key().name(), team.key().name())
            data["seed"] = mm.membership.seed + 1

            if match_up.match:
              team_record = match_up.match.get_team_records_query().filter(
                  "team =", mm.membership.team.key()).get()
              score = str(team_record.tds_for)
              if (match_up.winner.key() == mm.membership.key() and
                  (team_record.tds_for == team_record.tds_against or
                   match_up.match.disconnect)):
                score += "*"

              data["score"] = "<b>%s</b>" % score

            elif match_up.winner:
              # if there was a winner but no match then it was a forfeit
              if match_up.winner.key() == mm.membership.key():
                data["score"] = "&nbsp;"
              else:
                data["score"] = "<b><i>F</i></b>"

          team_data.append(data)

        if child == 0:
          arrow_class = "down_arrow"
        elif child == 1:
          arrow_class = "up_arrow"
        else:
          arrow_class = None

        match_data = match_up.match

        end_this_match = width_unit * round + match_width
        mid_next_match = width_unit * (round + 1) + match_width / 2
        arrow_width = mid_next_match - end_this_match

        match_up_data.append((round, team_data, position_left, arrow_width, arrow_class, match_data))

    # render and update
    #--------------------------------------------------------------------#

    tournament_box = misc.render('tournament_box.html', locals())
    if tournament.started:
      self.update(tournament_box, tournament.key())

    self.response.out.write(tournament_box)

