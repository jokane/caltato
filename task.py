#!/usr/bin/python


import gflags
import httplib2
import os
import sys
import re
import datetime

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

################################################################################
################################################################################
# From: https://developers.google.com/google-apps/tasks/instantiate
def getServices():
# Authenticate the user (possibly requiring them to authorize this app using
# their browser) and return a service object that can access that user's Task
# data.

  FLAGS = gflags.FLAGS

  # Set up a Flow object to be used if we need to authenticate. This
  # sample uses OAuth 2.0, and we set up the OAuth2WebServerFlow with
  # the information it needs to authenticate. Note that it is called
  # the Web Server Flow, but it can also handle the flow for native
  # applications
  # The client_id and client_secret are copied from the API Access tab on
  # the Google APIs Console
  FLOW = OAuth2WebServerFlow(
      client_id='xxxxx',
      client_secret='xxxxx',
      scope='https://www.googleapis.com/auth/tasks https://www.googleapis.com/auth/calendar',
      user_agent='task/0.1')

  # To disable the local server feature, uncomment the following line:
  FLAGS.auth_local_webserver = False

  # If the Credentials don't exist or are invalid, run through the native client
  # flow. The Storage object will ensure that if successful the good
  # Credentials will get written back to a file.
  storage = Storage(os.environ['HOME']+'/.task_credentials')
  credentials = storage.get()
  if credentials is None or credentials.invalid == True:
    credentials = run(FLOW, storage)

  # Create an httplib2.Http object to handle our HTTP requests and authorize it
  # with our good Credentials.
  http = httplib2.Http()
  http = credentials.authorize(http)

  # Build a service object for interacting with the API. Visit the Google APIs
  # Console to get a developerKey for your own application.
  calService = build(serviceName='calendar', version='v3', http=http);
  taskService = build(serviceName='tasks', version='v1', http=http);
  
  return (calService, taskService)



def fail(message):
  sys.stderr.write(message + "\n")
  sys.exit(1)

def main(args):
  (calService, taskService) = getServices()

  # When are we now?
  now = datetime.datetime.today()
  
  # Get the calendar events.
  token = None
  while True:
    events = calService.events().list(
      calendarId='primary',
      maxResults=10000,
      pageToken=token,
      singleEvents=True
    ).execute()

    for event in events['items']:
      summary = event.get('summary', '').encode('ascii', 'ignore')
      description = event.get('description', '').encode('ascii', 'ignore')
      for match in re.finditer(r"task(\(.*\))", description):
        # Remember the command we just found.
        command = match.group(1) 

        # Split it into an offset and a message.
        match = re.match("", command)

        # The results can contain either a date or a datetime, depending on
        # whether or not it's an all-day event.  These different kinds of
        # answers appear in differnent places in the 'start' hash.  Since we
        # only want the date part, extract just that.
        match = re.search(
          r"(\d\d\d\d)-(\d\d)-(\d\d)",
          event['start'].__repr__()
        )
        eventStart = datetime.date(
          int(match.group(1)),
          int(match.group(2)),
          int(match.group(3))
        )

        print "Summary: ", summary
        print "Command: ", match.group(0)
        print "Start: ", eventStart
        print 

    token = events.get('nextPageToken')
    if token is None:
     break


main(sys.argv)
