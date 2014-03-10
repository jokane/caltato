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
def getService():
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
      scope='https://www.googleapis.com/auth/tasks',
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

  # Build a service object for interacting with the API. Visit
  # the Google APIs Console
  # to get a developerKey for your own application.
  service = build(serviceName='tasks', version='v1', http=http);
  
  return service



def fail(message):
  sys.stderr.write(message + "\n")
  sys.exit(1)

def main(args):
  pass

main(sys.argv)
