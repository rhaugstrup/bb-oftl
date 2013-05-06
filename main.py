############# 
# Standard Python imports. 
import os 
import sys 
import logging 
#import gaepdb 
# Remove the standard version of Django 
#for k in [k for k in sys.modules if k.startswith('django')]: 
#    del sys.modules[k] 
############# 
from google.appengine.dist import use_library
use_library('django', '1.0')
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import grappl.handlers, views, cron
import callbacks.tournaments
import callbacks.coachs_page


application = webapp.WSGIApplication([
  # main tabs
  ('/recent_matches',      views.RecentMatches),
  ('/league_standings',    views.LeagueStandings),
  ('/coach_leaders',       views.CoachLeaders),  
  ('/team_leaders',        views.TeamLeaders),
  ('/player_leaders',      views.PlayerLeaders),
  ('/tournaments',         views.Tournaments),
  ('/coachs_page',         views.CoachsPage),

  # overlay boxes
  ('/team',       views.TeamBox),
  ('/coach',      views.CoachBox),
  ('/player',     views.PlayerBox),
  ('/match',      views.MatchBox),
  ('/tournament', views.TournamentBox),

  # tournament callbacks
  ('/get_trophy',          callbacks.tournaments.GetTrophy),
  ('/create_tournament',   callbacks.tournaments.Create),
  ('/enroll_team',         callbacks.tournaments.Enroll),
  ('/withdraw_team',       callbacks.tournaments.Withdraw),
  ('/force_withdraw',      callbacks.tournaments.ForceWithdraw),
  ('/start_tournament',    callbacks.tournaments.Start),
  ('/get_seeds',           callbacks.tournaments.GetSeeds),
  ('/seed_tournament',     callbacks.tournaments.SeedAndStart),
  ('/cancel_tournament',   callbacks.tournaments.Cancel),
  ('/forfeit_team',        callbacks.tournaments.Forfeit),

  # coach's page callbacks
  ('/register',            callbacks.coachs_page.Register),
  ('/claim_team',          callbacks.coachs_page.ClaimTeam),
  ('/get_bio',             callbacks.coachs_page.GetBio),
  ('/get_pic',             callbacks.coachs_page.GetPic),
  ('/get_logo',            callbacks.coachs_page.GetLogo),
  ('/change_bio',          callbacks.coachs_page.ChangeBio),
  ('/change_pic',          callbacks.coachs_page.ChangePic),
  ('/change_logo',         callbacks.coachs_page.ChangeLogo),
  ('/preregister_team',    callbacks.coachs_page.PreRegister),
  ('/retire_team',         callbacks.coachs_page.Retire),
  ('/clear_team_for_OFL',  callbacks.coachs_page.ClearForOFL),

  # GRAPPL handlers
  ('/grappl/submit',       grappl.handlers.Submit),
  ('/grappl/tasks/submit', grappl.handlers.SubmitTask),
  ('/grappl/tasks/update', grappl.handlers.UpdateTask),
  ('/grappl/bblog',        grappl.handlers.GetBBLog),

  # cron jobs
  ('/cron/retire_teams',   cron.RetireTeams),
  ], debug=True)


def main():
  webapp.template.register_template_library('templatetags')
  run_wsgi_app(application)


if __name__ == "__main__":
  main()


