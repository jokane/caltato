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
import datetime

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

################################################################################################
################################################################################################
bl = None
def getBackList():
  # Return a list of the tasks in the back list. 
  global bl

  if bl is not None:
    return bl

  bl = []
  service = getService()
  (front, back) = getListIDs()
  items = service.tasks().list(tasklist=back).execute().get('items', [])
  if items is not None:
    for taskDict in items:
      bl.append(Task.fromDict(taskDict))
  
  return bl
  
################################################################################################
################################################################################################

class Task:
  @classmethod
  def fromStrings(cls, _title, _repeat):
    r = cls();
    r.title = _title;
    r.repeat = _repeat;
    r.tid = None
    r.history = []
    r.dct = {}
    return r;

  @classmethod
  def fromDict(cls, dct):
    notes = eval(dct.get('notes', '{}'))
    r = cls();
    r.tid = dct['id']
    r.title = dct['title']
    r.repeat = notes.get('repeat', '')
    r.history = notes.get('history', '[]')
    r.dct = dct
    return r;

  def __str__(self):
    r = ""
    if self.tid is not None:
      r = r + "[" + self.tid[-6:] + "] "
    else:
      r = r + "[------]"
    r = r + self.repeat + ": " + self.title 
    if len(self.history) > 0:
      r += " (pushed " + ",".join(self.history) + ")"
    return r

  def store(self):
    # TODO: Logic to update instead of creating a new one.
    # (if tid is not None: ...)
    self.dct['title'] = self.title
    self.dct['notes'] = {
        'repeat': self.repeat,
        'history': self.history
      }.__repr__()
    service = getService()
    (front, back) = getListIDs()

    if self.tid is None:
      # Create a new backlist task.
      result = service.tasks().insert(tasklist=back, body=self.dct).execute()
      self.tid = result['id']
    else:
      # Update an existing task.
      service.tasks().update(tasklist=back, task=self.tid, body=self.dct).execute()

  def delete(self):
    service = getService()
    (front, back) = getListIDs()
    service.tasks().delete(tasklist=back, task=self.tid).execute()


  def due(self):
  # Is it time to insert this task into the front list?
  # Returns:
  #   True if the repeat string makes sense and it's time to push.
  #   False if the repeat string makes sense but it's not time to push.
  #   None if the repeat string does not make sense.

    # When did we last push this task?
    if len(self.history)==0:
      last = datetime.date.fromordinal(1)
    else:
      last = datetime.datetime.strptime(self.history[0], "%Y-%m-%d").date()

    # When are we now?
    today = datetime.date.today()

    
    # Try to match the repeat string.
    # 1. An exact date.
    match = re.match("(\d\d\d\d)-(\d\d)-(\d\d)", self.repeat)
    if match:
      when = datetime.datetime.strptime(self.repeat, "%Y-%m-%d").date()
      if(when > today):
        # Not time yet.
        return False
      elif(last >= when):
        # Already done.
        return False
      else:
        return True

    # Nothing matched.  The repeat specification is ill-formed.
    return None

  def push(self):
  # Insert this item into the front list.  Generally, this should only be
  # called only when self.due() is true.
    # TODO: Maintain a history of when this happened.
    # TODO: Update the backlist item to store the history
    # TODO: Use that history in due() above.
    # TODO: Use a shorter ID in the notes.
    service = getService()
    (front, back) = getListIDs()
    task = {
      'title' : self.title,
      'notes' : self.tid
    }
    service.tasks().insert(tasklist=front, body=task).execute()
    self.history.append(str(datetime.date.today()))

def addTask(args):
  # TODO: Reject duplicate titles.
  # TODO: Verify args.
  service = getService()
  (front, back) = getListIDs()
  repeat = args.pop(0)
  title = " ".join(args)
  task = Task.fromStrings(title, repeat)
  task.store()
  print task

def pushTasks(args):
  for task in getBackList():
    if task.due():
      task.push()
      task.store()
      print task

def showTasks(args):
  if len(args) == 0:
    pattern = ".*"
  else:
    pattern = "|".join(args)

  ok = False
  for task in getBackList():
    if(re.search(pattern, task.tid)):
      ok = True
      print task

  if(not ok): 
    fail("No tasks match " + pattern)

def deleteTask(args):
  pattern = args.pop(0)

  matches = []
  for task in getBackList():
    if(re.search(pattern, task.tid)):
      matches.append(task)
  
  if len(matches) == 0:
    fail("No match for " + pattern)
  elif len(matches) > 1:
    showTasks([pattern])
    fail("Multiple matches for " + pattern)
  else:
    matches[0].delete()
    print matches[0]


def fail(message):
  sys.stderr.write(message + "\n")
  sys.exit(1)

def main(args):
  script = args.pop(0)
  verb = args.pop(0)

  dispatch = {
    "add": addTask,
    "push": pushTasks,
    "show": showTasks,
    "delete": deleteTask
  }

  try:
    func = dispatch[verb]
  except KeyError:
    fail("Unknown verb: " + verb)

  func(args)

main(sys.argv)
