
import misc

class MatchData(object):

  def __init__(self, match, show_href=False):
    home_record, away_record = match.get_team_records_query().fetch(2)

    self.team_data = {}
    for which, record in (("home", home_record), ("away", away_record)):
      self.team_data[which] = {
          'team_href': record.team.get_box_href(),
          'record': record,
          'text_color': misc.get_contrasting_monochrome(record.team.color),
          }

    scorer_records = match.get_player_records_query().filter("tds_for >", 0)
    scorer_data = [
        ( r.tds_for if r.tds_for > 1 else None,
          0 if r.team_record.key() == home_record.key() else 1,
          r.player.get_box_anchor("match_players"))
      for r in scorer_records]

    self.disconnect = match.disconnect
    self.tournament_match_up = match.tournamentmatchup_set.get()
    self.scorer_data = scorer_data
    self.time = match.created.strftime("%A %B %d, %Y, %I:%M%p")

    if show_href:
      self.href = match.get_box_href()



