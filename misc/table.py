

class Column(object):
  def __init__(self, title, desc, getter, center=False, rowspan=1, divider=False):
    self.title   = title
    self.desc    = desc
    self.getter  = getter
    self.center  = center
    self.rowspan = rowspan
    self.divider = divider

class Table(object):
  def __init__(self, columns, query, id="", cls="", title=""):
    self.columns = columns
    self.id      = id
    self.cls     = cls
    self.rows    = []
    self.title   = title

    for entity in query:
      self.rows.append([(c.getter(entity), c) for c in columns])



