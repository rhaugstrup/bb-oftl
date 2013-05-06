import _winreg, msvcrt
import glob, re, traceback, httplib, urllib, sqlite3
import getpass, os, sys, socket
import hashlib


class MatchNotFound(Exception):
  pass

class ReplayNotFound(Exception):
  pass

class ReplaySubmitted(Exception):
  pass

class SubmitFailed(Exception):
  pass

class SubmitData(object):
  def __init__(self, post, replay):
    self.post   = post
    self.replay = replay


# -----------------------------------------------
# Converter functions / structures
# -----------------------------------------------

race_map = {
    1:  'Humans',
    2:  'Dwarves',
    3:  'Skaven',
    4:  'Orcs',
    5:  'Lizardmen',
    6:  'Goblins',
    7:  'Wood Elves',
    8:  'Chaos',
    9:  'Dark Elves',
    10: 'Undead',
    11: 'Halflings',
    12: 'Norse',
    13: 'Amazon',
    14: 'Pro Elves',
    15: 'High Elves',
    16: 'Khemri',
    17: 'Necromantic',
    18: 'Nurgle',
    19: 'Ogre',
    20: 'Vampire',
    21: 'Chaos Dwarves',
    22: 'Underworld',
    23: 'Khorne',
    }

position_map = {
    1:  'Lineman',
    2:  'Catcher',
    3:  'Thrower',
    4:  'Blitzer',
    5:  'Ogre',
    6:  'Blocker',
    7:  'Runner',
    8:  'Blitzer',
    9:  'Troll Slayer',
    10: 'Deathroller',
    11: 'Lineman',
    12: 'Catcher',
    13: 'Thrower',
    14: 'Wardancer',
    15: 'Treeman',
    16: 'Lineman',
    17: 'Thrower',
    18: 'Gutter Runner',
    19: 'Stormvermin',
    20: 'Rat Ogre',
    21: 'Lineman',
    22: 'Goblin',
    23: 'Thrower',
    24: 'Black Orc',
    25: 'Blitzer',
    26: 'Troll',
    27: 'Skink',
    28: 'Saurus',
    29: 'Kroxigor',
    30: 'Goblin',
    31: 'Looney',
    32: 'Beastman',
    33: 'Chaos Warrior',
    34: 'Minotaur',
    36: 'Grashnak Blackhoof',
    37: 'Griff Oberwald',
    38: 'Grim Ironjaw',
    39: 'Headsplitter',
    40: 'Jordell Freshbreeze',
    41: 'Ripper',
    42: 'Slibli',
    43: 'Varag Ghoul-Chewer',
    44: 'Troll',
    45: 'Pogoer',
    46: 'Fanatic',
    47: 'Lineman',
    48: 'Runner',
    49: 'Assassin',
    50: 'Blitzer',
    51: 'Witch Elf',
    52: 'Horkon Heartripper',
    53: "Morg 'N Thorg",
    54: 'Skeleton',
    55: 'Zombie',
    56: 'Ghoul',
    57: 'Wight',
    58: 'Mummy',
    59: 'Count Luther von Drakenborg',
    60: 'Halfling',
    61: 'Treeman',
    62: 'Lineman',
    63: 'Thrower',
    64: 'Runner',
    65: 'Berserker',
    66: 'Ulfwerener',
    67: 'Yhetee',
    68: 'Linewoman',
    69: 'Thrower',
    70: 'Catcher',
    71: 'Blitzer',
    72: 'Lineman',
    73: 'Thrower',
    74: 'Catcher',
    75: 'Blitzer',
    77: 'Lineman',
    78: 'Thrower',
    79: 'Catcher',
    80: 'Blitzer',
    81: 'Skeleton',
    82: 'Thro-Ras',
    83: 'Blitz-Ras',
    84: 'Tomb Guardian',
    86: 'Zombie',
    87: 'Ghoul',
    88: 'Wight',
    89: 'Flesh Golem',
    90: 'Werewolf',
    91: 'Rotter',
    92: 'Pestigor',
    93: 'Nurgle Warrior',
    94: 'Beast of Nurgle',
    95: 'Snotling',
    96: 'Ogre',
    97: 'Thrall',
    98: 'Vampire',
    99: 'Zara the Slayer',
    100: 'Scrappa Sorehead',
    101: 'Eldril Sidewinder',
    102: 'Lord Borak the Despoiler',
    103: 'Deeproot Strongbranch',
    104: 'Nekbrekerekh',
    105: 'Ramtut III',
    106: 'Icepelt Hammerblow',
    107: 'Bombardier',
    108: 'Hobgoblin',
    109: 'Blocker',
    110: 'Bull Centaur',
    111: 'Minotaur',
    123: 'Goblin',
    124: 'Skaven Lineman',
    125: 'Skaven Thrower',
    126: 'Skaven Blitzer',
    127: 'Warpstone Troll',
    129: 'Pit Fighter',
    130: 'Herald',
    131: 'Bloodletter',
    132: 'Bloodthirster',
    133: 'Bomber Dribblesnot',
    134: 'Zzharg Madeye',
    }

skill_map = {
    1:  'Strip Ball',
    2:  '+1 ST',
    3:  '+1 AG',
    4:  '+1 MA',
    5:  '+1 AV',
    6:  'Catch',
    7:  'Dodge',
    8:  'Sprint',
    9:  'Pass Block',
    10: 'Foul Appearance',
    11: 'Leap',
    12: 'Extra Arms',
    13: 'Mighty Blow',
    14: 'Leader',
    15: 'Horns',
    16: 'Two Heads',
    17: 'Stand Firm',
    18: 'Always Hungry',
    19: 'Regeneration',
    20: 'Take Root',
    21: 'Accurate',
    22: 'Break Tackle',
    23: 'Sneaky Git',
    25: 'Chainsaw',
    26: 'Dauntless',
    27: 'Dirty Player',
    28: 'Diving Catch',
    29: 'Dump-Off',
    30: 'Block',
    31: 'Bone-Head',
    32: 'Very Long Legs',
    33: 'Disturbing Presence',
    34: 'Diving Tackle',
    35: 'Fend',
    36: 'Frenzy',
    37: 'Grab',
    38: 'Guard',
    39: 'Hail Mary Pass',
    40: 'Juggernaut',
    41: 'Jump Up',
    44: 'Loner',
    45: 'Nerves of Steel',
    46: 'No Hands',
    47: 'Pass',
    48: 'Piling On',
    49: 'Prehensile Tail',
    50: 'Pro',
    51: 'Really Stupid',
    52: 'Right Stuff',
    53: 'Safe Throw',
    54: 'Secret Weapon',
    55: 'Shadowing',
    56: 'Side Step',
    57: 'Tackle',
    58: 'Strong Arm',
    59: 'Stunty',
    60: 'Sure Feet',
    61: 'Sure Hands',
    63: 'Thick Skull',
    64: 'Throw Team-Mate',
    67: 'Wild Animal',
    68: 'Wrestle',
    69: 'Tentacles',
    70: 'Multiple Block',
    71: 'Kick',
    72: 'Kick-Off Return',
    74: 'Big Hand',
    75: 'Claw',
    76: 'Ball & Chain',
    77: 'Stab', 
    78: 'Hypnotic Gaze',
    79: 'Stakes',
    80: 'Bombardier',
    81: 'Decay',
    82: "Nurgle's Rot",
    83: 'Titchy',
    84: 'BloodLust',
    85: 'Fan Favorite',
    86: 'Animosity',
    }

injury_map = {
    1:  'Badly Hurt',
    2:  'Broken Ribs',
    3:  'Groin Strain',
    4:  'Gouged Eye',
    5:  'Broken Jaw',
    6:  'Fractured Arm',
    7:  'Fractured Leg',
    8:  'Smashed Hand',
    9:  'Pinched Nerve',
    10: 'Damaged Back',
    11: 'Smashed Knee',
    12: 'Smashed Hip',
    13: 'Smashed Ankle',
    14: 'Serious Concussion',
    15: 'Fractured Skull',
    16: 'Broken Neck',
    17: 'Smashed Collar Bone',
    18: 'Dead',
    }

def get_ma(f):
  return int(float(f) / 8.33)

def get_st(f):
  return int((float(f) - 20.0) / 10)

def get_ag(f):
  return int(float(f) / 16.33)

def get_av(f):
  f = float(f)
  if f < 0.1:
    return 0
  elif f < 1.0:
    return 1
  elif f < 2.8:
    return 2
  elif f < 8.4:
    return 3
  elif f < 16.7:
    return 4
  elif f < 27.8:
    return 5
  elif f < 41.7:
    return 6
  elif f < 58.4:
    return 7
  elif f < 72.3:
    return 8
  elif f < 83.4:
    return 9
  elif f < 91.7:
    return 10
  elif f < 97.3:
    return 11
  else:
    return 12


# -----------------------------------------------
# Helper functions
# -----------------------------------------------

def get_y_or_n():
  char = ""
  while char != "y" and char != "n":
    char = msvcrt.getch().lower()
  return char


def submit(submit_data):

  submit_data.post['signature'] = ":".join([socket.gethostname(), getpass.getuser()])

  print "Contacting server and uploading...   ",

  http_conn    = httplib.HTTPConnection("localhost:8080")
  http_params  = urllib.urlencode(submit_data.post)
  http_headers = {
      "Content-Type": "application/x-www-form-urlencoded",
      "Accept": "text/plain",
      }
  http_conn.request("POST", "/grappl/submit", http_params, http_headers)

  response = http_conn.getresponse()
  http_conn.close()

  reason = response.read()
  if not reason:
    reason = (
        "Unknown.  Most likely the server was temporarily unable to serve \n"
        "your request.  Please try to resubmit. If the problem persists, \n"
        "please follow the instructions below.")

  if response.status != 200:
    print "failed."
    print
    print "Submit failed with reason:"
    print "  {0}".format(reason)
    print
    print "Please copy/paste the contents of this window and PM to elessar9 in the"
    print "OFL forums.  Please be sure to describe any unusual circumstances"
    print "surrounding this submit attempt."

    raise SubmitFailed

  print "success."
  print
  print "All done."

  # write the replay name to the replays_submitted file
  f = open(replays_submitted, "a+")
  f.write("{0}\n".format(submit_data.replay))
  f.close()


def prepare_submit():

  # Get a handle on the MatchReport.sqlite file
  # -------------------------------------------

  print
  print "Searching for MatchReport.sqlite file...."

  if not os.path.exists(match_report):
    print "MatchReport.sqlite not found!"
    raise MatchNotFound()

  match_db = sqlite3.connect(match_report)
  match_db.row_factory = sqlite3.Row

  cursor = match_db.execute("""
      SELECT idTeam_Listing_Home, idTeam_Listing_Away, Home_iScore, Away_iScore
      FROM Calendar""")
  home_id, away_id, home_score, away_score = cursor.fetchone()

  away_team = match_db.execute("SELECT strName FROM Away_Team_Listing").fetchone()[0]
  home_team = match_db.execute("SELECT strName FROM Home_Team_Listing").fetchone()[0]

  print "Found for the following match:"
  print
  print "{0} {1} - {2} {3}".format(home_team, home_score, away_team, away_score)
  print
  print "Is this the match you wish to report? [y/n]"

  if get_y_or_n() == "n":
    return None

  # Get a handle on the Replay file
  # -------------------------------------------

  print "Searching for matching replay file...",

  replays = [os.path.join(replay_dir, r) for r in os.listdir(replay_dir)]
  for replay in sorted(replays,
                      key=lambda r: os.stat(r).st_mtime,
                      reverse=True):

    root, ext = os.path.splitext(replay)
    if ext != ".db":
      continue

    replay_db = sqlite3.connect(replay)
    cursor = replay_db.execute("""
        SELECT idTeam_Listing_Home, idTeam_Listing_Away
        FROM Calendar""")

    replay_home_id, replay_away_id = cursor.fetchone()
    if home_id == replay_home_id and away_id == replay_away_id:
      # we got it (or at least, we will assume this is it since it is the most
      # recent match these two teams played)
      # TODO: make this more robust
      break

  else:
    print "not found!"
    raise ReplayNotFound

  if os.path.exists(replays_submitted):
    with open(replays_submitted, "r") as f:
      for line in f:
        if line.strip() == replay:
          print "already submitted!"
          raise ReplaySubmitted

  print "found."

  # Handle disconnects
  # -------------------------------------------

  home_cursor = match_db.execute("""
      SELECT * FROM Home_Statistics_Players WHERE iMVP = 1""")
  away_cursor = match_db.execute("""
      SELECT * FROM Away_Statistics_Players WHERE iMVP = 1""")

  disconnect = (
      home_cursor.fetchone() == None or
      away_cursor.fetchone() == None)

  if disconnect:
    print
    print "This match was a disconnect.  Were you the one who got disconnected? [y/n]"
    print
    if get_y_or_n() == "y":
      return None

  # Read the other data from sqlite
  # --------------------------------------------

  print "Packaging up submit data...          ",

  home_data = {}
  away_data = {}

  md5 = hashlib.md5()

  for which, data in (("Home", home_data), ("Away", away_data)):

    # team information
    # ----------------
    
    cursor = match_db.execute("""
        SELECT strName, idRaces, iValue, iCash, iPopularity,
               iRerolls, bApothecary, iCheerleaders, iAssistantCoaches,
               strLogo, iTeamColor
        FROM {0}_Team_Listing""".format(which))
    row = cursor.fetchone()

    data["name"]    = row[0].encode('utf-8')
    data["race"]    = race_map[row[1]]
    data["tv_for"]  = row[2]
    data["cash"]    = row[3]
    data["ff"]      = row[4]
    data["rerolls"] = row[5]
    data["apoths"]  = row[6]
    data["cheers"]  = row[7]
    data["coaches"] = row[8]
    data["logo"]    = row[9]
    data["color"]   = row[10]

    # update the hash with high level information
    for atom in row:
      md5.update(str(atom))

    # player information
    # ------------------

    cursor = match_db.execute("""
        SELECT * FROM {0}_Player_Listing""".format(which))

    for player in cursor:
      player_id = player["ID"]
      i = player_id

      data["p{0}_bb_id".format(i)]     = player_id
      data["p{0}_name".format(i)]      = player["strName"].encode('utf-8')
      data["p{0}_position".format(i)]  = position_map[player["idPlayer_Types"]]
      data["p{0}_number".format(i)]    = player["iNumber"]

      data["p{0}_mv".format(i)]        = get_ma(player["Characteristics_fMovementAllowance"])
      data["p{0}_st".format(i)]        = get_st(player["Characteristics_fStrength"])
      data["p{0}_ag".format(i)]        = get_ag(player["Characteristics_fAgility"])
      data["p{0}_av".format(i)]        = get_av(player["Characteristics_fArmourValue"])
      data["p{0}_level".format(i)]     = player["idPlayer_Levels"]
      data["p{0}_spp".format(i)]       = player["iExperience"]
      data["p{0}_value".format(i)]     = player["iValue"]

      cursor = match_db.execute("""
          SELECT idPlayer_Casualty_Types
          FROM {0}_Player_Casualties
          WHERE idPlayer_Listing = {1}""".format(which, player_id))
      injuries = [injury_map[injury[0]] for injury in cursor]

      injury_string = ",".join(injuries)
      data["p{0}_match_injuries".format(i)] = injury_string

      cursor = replay_db.execute("""
          SELECT idPlayer_Casualty_Types
          FROM {0}_Player_Casualties
          WHERE idPlayer_Listing = {1}""".format(which, player_id))
      injuries = [injury_map[injury[0]] for injury in cursor]

      injury_string = ",".join(injuries)
      data["p{0}_injuries".format(i)] = injury_string

      cursor = replay_db.execute("""
          SELECT idSkill_Listing
          FROM {0}_Player_Type_Skills
          WHERE idPlayer_Types = {1}""".format(which, player["idPlayer_Types"]))
      skills = [skill_map[skill[0]] for skill in cursor]

      cursor = replay_db.execute("""
          SELECT idSkill_Listing
          FROM {0}_Player_Skills
          WHERE idPlayer_Listing = {1}""".format(which, player_id))
      skills.extend([skill_map[skill[0]] for skill in cursor])

      skill_string = ",".join(skills)
      data["p{0}_skills".format(i)] = skill_string

    cursor = match_db.execute("""
        SELECT * FROM {0}_Statistics_Players""".format(which))

    for player_stats in cursor:
      i = player_stats['idPlayer_Listing']
      if i == 0:
        continue

      # update hash with stat information
      for atom in player_stats:
        md5.update(str(atom))

      data["p{0}_played".format(i)]        = player_stats['iMatchPlayed']
      data["p{0}_mvps".format(i)]          = player_stats['iMVP']
      data["p{0}_tds_for".format(i)]       = player_stats['Inflicted_iTouchdowns']
      data["p{0}_passes_for".format(i)]    = player_stats['Inflicted_iPasses']
      data["p{0}_pyards_for".format(i)]    = player_stats['Inflicted_iMetersPassing']
      data["p{0}_rec_for".format(i)]       = player_stats['Inflicted_iCatches']
      data["p{0}_ryards_for".format(i)]    = player_stats['Inflicted_iMetersRunning']
      data["p{0}_int_for".format(i)]       = player_stats['Inflicted_iInterceptions']
      data["p{0}_int_against".format(i)]   = player_stats['Sustained_iInterceptions']
      data["p{0}_tckl_for".format(i)]      = player_stats['Inflicted_iTackles']
      data["p{0}_tckl_against".format(i)]  = player_stats['Sustained_iTackles']
      data["p{0}_kills_for".format(i)]     = player_stats['Inflicted_iDead']
      data["p{0}_kills_against".format(i)] = player_stats['Sustained_iDead']
      data["p{0}_cas_for".format(i)]       = player_stats['Inflicted_iCasualties']
      data["p{0}_cas_against".format(i)]   = player_stats['Sustained_iCasualties']
      data["p{0}_ko_for".format(i)]        = player_stats['Inflicted_iKO']
      data["p{0}_ko_against".format(i)]    = player_stats['Sustained_iKO']
      data["p{0}_stun_for".format(i)]      = player_stats['Inflicted_iStuns']
      data["p{0}_stun_against".format(i)]  = player_stats['Sustained_iStuns']
      data["p{0}_inj_for".format(i)]       = player_stats['Inflicted_iInjuries']
      data["p{0}_inj_against".format(i)]   = player_stats['Sustained_iInjuries']

  # Fill in the post fields
  # -----------------------

  post_data = {}
  post_data['md5'] = md5.hexdigest()

  if disconnect:
    post_data['disconnect'] = True

  # copy home and away data into post
  for k, v in sorted(home_data.items()):
    post_data['home_{0}'.format(k)] = v
  for k, v in sorted(away_data.items()):
    post_data['away_{0}'.format(k)] = v

  # copy tv 
  post_data['home_tv_against'] = post_data["away_tv_for"]
  post_data['away_tv_against'] = post_data["home_tv_for"]

  # compute result
  if home_score > away_score:
    post_data['home_result'] = 1
  elif home_score < away_score:
    post_data['home_result'] = -1
  else:
    post_data['home_result'] = 0
  post_data['away_result'] = -post_data['home_result']

  print "done."

  return SubmitData(post_data, replay)


# -----------------------------------------------
# Main
# -----------------------------------------------

if __name__ == '__main__':
  try:
    registry_key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
        "SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
    my_documents, _ = _winreg.QueryValueEx(registry_key, "Personal")
    bloodbowl_dir = "BloodBowl"	
    numdirs = 0
    if os.path.exists(os.path.join(my_documents, "BloodBowlChaos")):
      bloodbowl_CE_dir = "BloodBowlChaos"
      match_report_CE = os.path.join(my_documents, bloodbowl_CE_dir, "MatchReport.sqlite")
      if os.path.exists(match_report_CE):
        bloodbowl_dir = "BloodBowlChaos"
        numdirs = numdirs + 1
    if os.path.exists(os.path.join(my_documents, "BloodBowlLegendary")):
      bloodbowl_LE_dir = "BloodBowlLegendary"
      match_report_LE = os.path.join(my_documents, bloodbowl_LE_dir, "MatchReport.sqlite")
      if os.path.exists(match_report_LE):
        bloodbowl_dir = "BloodBowlLegendary"
        numdirs = numdirs + 1
    #If both LE and CE, search for the most recent match report
    if numdirs == 2:
      if os.stat(match_report_LE).st_mtime > os.stat(match_report_CE).st_mtime:
        bloodbowl_dir = "BloodBowlLegendary"
      else:
        bloodbowl_dir = "BloodBowlChaos"
    match_report = os.path.join(my_documents, bloodbowl_dir, "MatchReport.sqlite")
    replay_dir   = os.path.join(my_documents, bloodbowl_dir, "Saves", "Replays")
    replays_submitted = os.path.join(replay_dir, "TEST_Submitted.txt")

    submit_data = prepare_submit()
    if (submit_data):
      submit(submit_data)

    return_code = 0

  except (MatchNotFound, ReplayNotFound, ReplaySubmitted, SubmitFailed):
    print
    print "Aborting!"
    return_code = -1

  except:
    print
    print "Received a fatal exception!"
    print
    print traceback.format_exc()
    print
    print ("If you believe the submitter is in error, "
        "please report to masher in the OFL forums.")
    return_code = -2

  print
  print "Press any key to close this window."
  msvcrt.getch()
  sys.exit(return_code)

