
from google.appengine.ext import webapp
from google.appengine.api import mail

from grappl.submit import prepare_submit, process_submit, process_update
import models


class Submit(webapp.RequestHandler):

  def post(self):

    data = {}
    for arg in self.request.arguments():
      data[arg] = self.request.get(arg)

    try:
      prepare_submit(data, self)
    except Exception, e:
      mail.send_mail(
          sender="grappl@bb-oftl.appspotmail.com",
          to="rhaugstrup@gmail.com",
          subject="bb-oftl: preparation error!",
          body="Failed with exception: %s" % e)
      raise


class SubmitTask(webapp.RequestHandler):

  def post(self):

    submit_data_key_string = self.request.get("submit_data_key_string")
    submit_data = models.SubmitData.get(submit_data_key_string)
    localtest   = bool(self.request.get("localtest"))

    match_lookup = submit_data.parent().parent()

    try:
      process_submit(submit_data, localtest)
    except Exception, e:
      mail.send_mail(
          sender="grappl@bb-oftl.appspotmail.com",
          to="rhaugstrup@gmail.com",
          subject="bb-oftl: submit error for %s!" % match_lookup.get_string(),
          body="Failed with exception: %s" % e)

      # In this case we reraise to allow the task to recover itself.
      # This is OK because the task is idempotent!
      raise


class UpdateTask(webapp.RequestHandler):

  def post(self):

    match_key_string = self.request.get("match_key_string")
    match = models.Match.get(match_key_string)
    match_lookup = match.parent()

    try:
      process_update(match)
    except Exception, e:
      mail.send_mail(
          sender="grappl@bb-oftl.appspotmail.com",
          to="rhaugstrup@gmail.com",
          subject="bb-oftl: update error for %s!" % match_lookup.get_string(),
          body="Failed with exception: %s" % e)

      # In this case we reraise to allow the task to recover itself.
      # This is OK because the task is idempotent!
      raise


class GetBBLog(webapp.RequestHandler):
  def get(self):
    n = self.request.get("n")
    try:
      bblog = (models.SubmitData.all()
          .order('-uploaded')
          .fetch(1, offset=int(n))[0].bblog)
    except:
      bblog = "N/A"
    self.response.out.write(bblog)


