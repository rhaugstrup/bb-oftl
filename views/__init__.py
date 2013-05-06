
from google.appengine.api import memcache
from google.appengine.ext import webapp

class CachedView(webapp.RequestHandler):

  @classmethod
  def emit(cls, out, key=""):
    memcache_key = cls.__name__ + str(key)
    cache = memcache.get(memcache_key)
    hit = cache is not None
    if hit:
      out.write(cache)
    return hit

  @classmethod
  def update(cls, new, key=""):
    memcache_key = cls.__name__ + str(key)
    try:
      memcache.add(memcache_key, new)
    except ValueError:
      pass
  
  @classmethod
  def clear(cls, key=""):
    memcache_key = cls.__name__ + str(key)
    memcache.delete(memcache_key)


from league_standings import *
from player_box import *
from player_leaders import *
from recent_matches import *
from match_box import *
from team_box import *
from coach_box import *
from team_leaders import *
from coach_leaders import *
from coachs_page import *
from tournaments import *
from tournament_box import *

