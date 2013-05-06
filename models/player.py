
from google.appengine.ext import db
import logging

from models import Team


class Injury(db.Model):
  # key_name = injury
  effect    = db.StringProperty()
  mng       = db.BooleanProperty()
  permanent = db.BooleanProperty()

  @staticmethod
  def init():
    for key_name, effect, mng, permanent in [
        ("Badly Hurt", "No Lasting Effect", False, False),
        ("Broken Ribs", "Miss Next Game", True, False),
        ("Groin Strain", "Miss Next Game", True, False),
        ("Gouged Eye", "Miss Next Game", True, False),
        ("Broken Jaw", "Miss Next Game", True, False),
        ("Fractured Arm", "Miss Next Game", True, False),
        ("Fractured Leg", "Miss Next Game", True, False),
        ("Smashed Hand", "Miss Next Game", True, False),
        ("Pinched Nerve", "Miss Next Game", True, False),
        ("Damaged Back", "Niggling Injury", True, True),
        ("Smashed Knee", "Niggling Injury", True, True),
        ("Smashed Hip", "-1 MA", True, True),
        ("Smashed Ankle", "-1 MA", True, True),
        ("Serious Concussion", "-1 AV", True, True),
        ("Fractured Skull", "-1 AV", True, True),
        ("Broken Neck", "-1 AG", True, True),
        ("Smashed Collar Bone", "-1 ST", True, True),
        ("Dead", "Dead", False, True)]:
      Injury(
          key_name  = key_name,
          effect    = effect,
          mng       = mng,
          permanent = permanent).put()


class Position(db.Model):
  # key_name = position
  starplayer = db.BooleanProperty()

  @staticmethod
  def init():
    for key_name, starplayer in [
        ('Lineman', False),
        ('Catcher', False),
        ('Thrower', False),
        ('Ogre', False),
        ('Blitzer', False),
        ('Blocker', False),
        ('Runner', False),
        ('Troll Slayer', False),
        ('Deathroller', False),
        ('Wardancer', False),
        ('Treeman', False),
        ('Gutter Runner', False),
        ('Stormvermin', False),
        ('Rat Ogre', False),
        ('Goblin', False),
        ('Black Orc', False),
        ('Troll', False),
        ('Skink', False),
        ('Saurus', False),
        ('Kroxigor', False),
        ('Goblin', False),
        ('Looney', False),
        ('Beastman', False),
        ('Chaos Warrior', False),
        ('Minotaur', False),
        ('Grashnak Blackhoof', True),
        ('Griff Oberwald', True),
        ('Grim Ironjaw', True),
        ('Headsplitter', True),
        ('Jordell Freshbreeze', True),
        ('Ripper', True),
        ('Slibli', True),
        ('Varag Ghoul-Chewer', True),
        ('Troll', False),
        ('Pogoer', False),
        ('Fanatic', False),
        ('Assassin', False),
        ('Witch Elf', False),
        ('Horkon Heartripper', True),
        ("Morg 'N Thorg", True),
        ('Skeleton', False),
        ('Zombie', False),
        ('Ghoul', False),
        ('Wight', False),
        ('Mummy', False),
        ('Count Luther von Drakenborg', True),
        ('Halfling', False),
        ('Berserker', False),
        ('Ulfwerener', False),
        ('Yhetee', False),
        ('Linewoman', False),
        ('Thro-Ras', False),
        ('Blitz-Ras', False),
        ('Tomb Guardian', False),
        ('Wight', False),
        ('Flesh Golem', False),
        ('Werewolf', False),
        ('Rotter', False),
        ('Pestigor', False),
        ('Nurgle Warrior', False),
        ('Beast of Nurgle', False),
        ('Snotling', False),
        ('Thrall', False),
        ('Vampire', False),
        ('Zara the Slayer', True),
        ('Scrappa Sorehead', True),
        ('Eldril Sidewinder', True),
        ('Lord Borak the Despoiler', True),
        ('Deeproot Strongbranch', True),
        ('Nekbrekerekh', True),
        ('Ramtut III', True),
        ('Icepelt Hammerblow', True),
        ('Bombardier', False),
        ('Hobgoblin', False),
        ('Bull Centaur', False),
        ('Skaven Lineman', False),
        ('Skaven Thrower', False),
        ('Skaven Blitzer', False),
        ('Warpstone Troll', False),
        ('Pit Fighter', False),
        ('Herald', False),
        ('Bloodletter', False),
        ('Bloodthirster', False),
        ('Bomber Dribblesnot', True),
        ('Zzharg Madeye', True)]:
      Position(
          key_name   = key_name,
          starplayer = starplayer).put()


class Skill(db.Model):
  # key_name = skill

  @staticmethod
  def init():
    for key_name in [
        'Strip Ball',
        '+1 ST',
        '+1 AG',
        '+1 MA',
        '+1 AV',
        'Catch',
        'Dodge',
        'Sprint',
        'Pass Block',
        'Foul Appearance',
        'Leap',
        'Extra Arms',
        'Mighty Blow',
        'Leader',
        'Horns',
        'Two Heads',
        'Stand Firm',
        'Always Hungry',
        'Regeneration',
        'Take Root',
        'Accurate',
        'Break Tackle',
        'Sneaky Git',
        'Chainsaw',
        'Dauntless',
        'Dirty Player',
        'Diving Catch',
        'Dump-Off',
        'Block',
        'Bone-Head',
        'Very Long Legs',
        'Disturbing Presence',
        'Diving Tackle',
        'Fend',
        'Frenzy',
        'Grab',
        'Guard',
        'Hail Mary Pass',
        'Juggernaut',
        'Jump Up',
        'Loner',
        'Nerves of Steel',
        'No Hands',
        'Pass',
        'Piling On',
        'Prehensile Tail',
        'Pro',
        'Really Stupid',
        'Right Stuff',
        'Safe Throw',
        'Secret Weapon',
        'Shadowing',
        'Side Step',
        'Tackle',
        'Strong Arm',
        'Stunty',
        'Sure Feet',
        'Sure Hands',
        'Thick Skull',
        'Throw Team-Mate',
        'Wild Animal',
        'Wrestle',
        'Tentacles',
        'Multiple Block',
        'Kick',
        'Kick-Off Return',
        'Big Hand',
        'Claw',
        'Ball & Chain',
        'Stab',
        'Hypnotic Gaze',
        'Stakes',
        'Bombardier',
        'Decay',
        "Nurgle's Rot",
        'Titchy',
        'BloodLust',
        'Fan Favorite',
        'Animosity']:
      Skill(key_name = key_name).put()


class PlayerStats(db.Model):
  played           = db.IntegerProperty(default=0)
  mvps             = db.IntegerProperty(default=0)
  tds_for          = db.IntegerProperty(default=0)
  passes_for       = db.IntegerProperty(default=0)
  pyards_for       = db.IntegerProperty(default=0)
  rec_for          = db.IntegerProperty(default=0)
  ryards_for       = db.IntegerProperty(default=0)
  int_for          = db.IntegerProperty(default=0)
  int_against      = db.IntegerProperty(default=0)
  kills_for        = db.IntegerProperty(default=0)
  kills_against    = db.IntegerProperty(default=0)
  cas_for          = db.IntegerProperty(default=0)
  cas_against      = db.IntegerProperty(default=0)
  ko_for           = db.IntegerProperty(default=0)
  ko_against       = db.IntegerProperty(default=0)
  stun_for         = db.IntegerProperty(default=0)
  stun_against     = db.IntegerProperty(default=0)
  tckl_for         = db.IntegerProperty(default=0)
  tckl_against     = db.IntegerProperty(default=0)

  def accumulate(self, player_stats):
    for property in PlayerStats.properties():
      setattr(self, property,
          getattr(self, property) +
          getattr(player_stats, property))

  def is_empty(self):
    for property in PlayerStats.properties():
      if getattr(self, property) != 0:
        return False
    return True

  def reset(self):
    for property in PlayerStats.properties():
      setattr(self, property, 0)

  def compute_spp(self):
    return sum([
      self.mvps * 5,
      self.tds_for * 3,
      self.cas_for * 2,
      self.int_for * 2,
      self.passes_for * 1,
      ])


class PlayerProfile(db.Model):
  # default is for initial expected spp
  spp      = db.IntegerProperty(default=0)  
  level    = db.IntegerProperty()
  mv       = db.IntegerProperty()
  st       = db.IntegerProperty()
  ag       = db.IntegerProperty()
  av       = db.IntegerProperty()
  value    = db.IntegerProperty()
  skills   = db.ListProperty(db.Key)
  injuries = db.ListProperty(db.Key)

  def update(self, player_profile):
    for property in PlayerProfile.properties():
      setattr(self, property, getattr(player_profile, property))


class PlayerPicture(db.Model):
  # key_name = player bb_id
  box     = db.BlobProperty()
  leader  = db.BlobProperty()
  thumb   = db.BlobProperty()


class Player(PlayerStats, PlayerProfile):
  # key_name = bb_id
  name      = db.StringProperty()
  position  = db.ReferenceProperty(Position)
  team      = db.ReferenceProperty(Team)
  number    = db.IntegerProperty(indexed=False)

  matches           = db.IntegerProperty(default=0)
  retired           = db.BooleanProperty(default=False)
  missing_next_game = db.BooleanProperty(default=False)
  level_up_pending  = db.BooleanProperty(default=False)

  # coach preferences
  bio = db.TextProperty(default="")
  pic = db.ReferenceProperty(PlayerPicture)

  def get_pic_url(self, size="box"):
    if self.pic:
      return 'get_pic?player_key=%s&size=%s' % (self.key(), size)
    else:
      subdir = ""
      if size == "leader":
        subdir = "leader/"

      return 'images/positions/%s%s-%s.jpg' % (
          subdir,
          self.team.race.key().name().lower().replace(" ", ""),
          self.position.key().name().lower().replace(" ", ""))
  
  def get_box_pic_url(self):
    return self.get_pic_url("box")

  def get_leader_pic_url(self):
    return self.get_pic_url("leader")

  @classmethod
  def create(cls, bb_id, name, position, team, number):
    verified = True

    if bb_id < 16:
      # journeyman/starplayer
      key_name = None
      player = None
      team = None
    else:
      key_name = str(bb_id)
      player = cls.get_by_key_name(key_name)

    if player is None:
      player = cls(
          key_name = key_name,
          name     = name,
          position = position,
          team     = team,
          number   = number)
      player.put()

    return player

  def update(self, record):
    super(Player, self).update(record)
    self.accumulate(record)
    self.injuries.extend(record.match_injuries)
    self.matches += 1

    tv_delta = 0

    # all mng players are now back in action
    self.missing_next_game = False
    if not record.played:
      tv_delta += record.value

    # deaths / mng injuries
    for injury_key in record.match_injuries:
      if Injury.get(injury_key).mng:
        self.missing_next_game = True
      elif injury_key.name() == "Dead":
        self.retired = True
        tv_delta -= record.value

    # SPP and level adjustments
    old_spp = self.spp
    self.spp = old_spp + record.compute_spp()
    self.level_up_pending = False

    for level_cut_off in [6, 16, 31, 51, 76, 176]:
      if old_spp < level_cut_off and self.spp >= level_cut_off:
        self.level += 1
        self.level_up_pending = True
      
        # estimate new player value
        if self.value: # legacy check
          self.value += 20
        tv_delta += 20
    
    return tv_delta

  def recompute(self):
    # everything that is a read-modify-write update must be reset
    self.matches = 0

    self.reset()
    for record in self.playerrecord_set.order('created'):
      self.update(record)

  def get_box_href(self):
    return '#player?player_key_name=%s' % self.key().name()

  def get_box_anchor(self, rel):
      if self.key().name():
        return '<a rel="%s" href="%s">%s</a>' % (
            rel, self.get_box_href(), self.name)
      elif self.position.starplayer:
        return "<b>" + self.name + "</b>"
      else:
        return "<b>" + self.name + "</b> <i>(Journeyman)</i>"



