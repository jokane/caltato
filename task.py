#!/usr/bin/python


# Use two lists: 
# - Main list: Seen by user.
# - Back list: Used for storage.
# Verbs:
# - push: Check for tasks from back list that should be added to main list
# - now: Add a task to main list immedidately
# - future: Add a task to the back list, to be moved to main list at a given date in the future.
# - list: Show tasks in the back list, with a unique ID for each one.
# - update: Change the description or recurrence options of a back list item, identified by its unique ID.
# - delete: Remove a back list item.
# Recurrence options:
# - once(date)
# - month(dayOfMonth[,numberOfMonths=1])
# - year(date)
# - week(dayOfWeek)

import gflags
import httplib2
import os
import sys
import re

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

################################################################################
################################################################################
# From: https://developers.google.com/google-apps/tasks/instantiate
service = None
def getService():
# Authenticate the user (possibly requiring them to authorize this app using
# their browser) and return a service object that can access that user's Task
# data.

  global service

  if service is not None:
    return service

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


################################################################################################
front = None
back = None
def getListIDs():
  # Get and return the IDs for the user's front and back lists.
  global front, back
  if(front is None or back is None):
    service = getService() 
    tasklists = service.tasklists().list().execute()
    for tasklist in tasklists['items']:
      if(tasklist['title'] == "Jason's list"):
        front = tasklist['id']
      if(tasklist['title'] == "Back list"):
        back = tasklist['id']
  return (front, back)


def expandShortTID(shortTID):
  tids = []
  service = getService()
  (front, back) = getListIDs()
  for taskDict in service.tasks().list(tasklist=back).execute()['items']:
    if re.search(shortTID, taskDict['id']):
      tids.append(taskDict['id'])
  if(len(tids) == 0):
    fail("No tasks match " + shortTID)
  return tids

class Task:
  @classmethod
  def fromStrings(cls, _text, _repeat):
    r = cls();
    r.text = _text;
    r.repeat = _repeat;
    r.tid = None
    return r;

  @classmethod
  def fromDict(cls, dct):
    notes = eval(dct.get('notes', '{}'))
    r = cls();
    r.tid = dct['id']
    r.text = dct['title']
    r.repeat = notes.get('repeat', '')
    return r;

  @classmethod
  def fromTID(cls, tid):
    service = getService()
    (front, back) = getListIDs()
    dct = service.tasks().get(tasklist=back, task=tid).execute()
    return Task.fromDict(dct)

  def __str__(self):
    if self.tid is not None:
      return "[" + self.tid[-6:] + "] " + self.repeat + ": " + self.text
    else:
      return "[------] " + self.repeat + ": " + self.text


  def store(self):
    # TODO: Logic to update instead of creating a new one.
    # (if tid is not None: ...)
    task = {
      'title' : self.text,
      'notes' : {
        'repeat': self.repeat
      }.__repr__()
    }
    service = getService()
    (front, back) = getListIDs()
    result = service.tasks().insert(tasklist=back, body=task).execute()
    self.tid = result['id']


def addTask(args):
  # TODO: Reject duplicate texts.
  # TODO: Verify args.
  service = getService()
  (front, back) = getListIDs()
  repeat = args.pop(0)
  text = " ".join(args)
  task = Task.fromStrings(text, repeat)
  task.store()
  print task

def listTasks(args):
  service = getService()
  (front, back) = getListIDs()
  for taskDict in service.tasks().list(tasklist=back).execute()['items']:
    task = Task.fromDict(taskDict)
    print task

    task = Task.fromDict(taskDict)



def pushTasks(args):
  pass

def showTask(args):
  shortTID = args.pop(0)
  service = getService()
  (front, back) = getListIDs()
  
  tids = expandShortTID(shortTID, service)
  for tid in tids:
    task = Task.fromTID(tid)
    print task

def deleteTask(args):
  shortTID = args.pop(0)
  service = getService()
  (front, back) = getListIDs()
  tids = expandShortTID(shortTID)
  if len(tids) > 1:
    showTask([shortTID])
    fail("Multiple matches for " + shortTID)
  else:
    service.tasks().delete(tasklist=back, task=tids[0]).execute() 


def fail(message):
  sys.stderr.write(message + "\n")
  sys.exit(1)

def main(args):
  script = args.pop(0)
  verb = args.pop(0)

  dispatch = {
    "add": addTask,
    "push": pushTasks,
    "list": listTasks,
    "show": showTask,
    "delete": deleteTask
  }

  try:
    func = dispatch[verb]
  except KeyError:
    fail("Unknown verb: " + verb)

  func(args)

main(sys.argv)
