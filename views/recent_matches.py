
from google.appengine.ext import webapp

import misc, views
from models import Match

from misc.match_data import MatchData

class RecentMatches(views.CachedView):

  def get(self):

    # check for a cached version
    #--------------------------------------------------------------------#

    if self.emit(self.response.out):
      return

    # not cached or evicted from cache; regenerate
    #--------------------------------------------------------------------#

    matches_data = []
    for match in Match.all().filter('processed =', True).order('-created').fetch(10):
      matches_data.append(MatchData(match, show_href=True))

    # render and update 
    #--------------------------------------------------------------------#

    recent_matches = misc.render('recent_matches.html', locals())
    self.update(recent_matches)

    self.response.out.write(recent_matches)


