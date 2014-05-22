# caltato
This script automates the creation of Google Tasks items, using comments
embedded in other Google Tasks and in Google Calendar events.  The goal is to
keep one's task list short and uncluttered, adding new items only when they
require one's attention.


## Calendar Tasks
To create a task on a specific date, create a Google Calendar event on that
date and include a line like this in its description field:

    task: Do something.

On the date associated with that event, caltato will create a task telling you
to "Do something".  Multiple task lines are allowed in each event.

You can also provide an offset, in days, from the event's date.  For example,
when I give an exam in my classes, the event's description has these lines, to
remind me to prepare the exam beforehand and grade the exam afterward:

     task: -3 Prepare exam.
     task: +1 Grade exam.

Repeating events are handled correctly.  For example, one might create an
annually-repeating event called "Anniversary" with a reminder like this:

     task: -7 Order flowers.

## Zombie Tasks
For a task that should be redone periodically, add a `zombie` line to its notes
field, specifying the number of days after its completion that the task should
return.  For example, a task called "Call Mom" might have this line in its
notes:

    zombie: 7

Seven days after that task is marked as complete, caltato will create a new,
not-yet-complete task with the same name and the same notes (including,
crucially, the `zombie` tag).

There's some similarity between creating a zombie task and adding a calendar
task to a repeating event.  The key difference is that zombie tasks reappear a
certain amount of time after they're *completed*, rather than on pre-specified
dates.  This is important if there's some delay between creating a task and
completing it.

## Usage
Run once per day, with `-c` for calendar tasks and `-z` for zombie tasks.

For example, I use this crontab line to check for both kinds of tasks early
each morning:

    30 5 * * * projects/caltato/caltato -c -z >> ~/.caltato/output 2>&1


