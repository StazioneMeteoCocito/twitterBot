# before starting, git pull in dati must be performed
import calendar
import datetime
import json
import math
import os
import datetime

import DataLibrary

tw = DataLibrary.Tweet(os.environ)

now = datetime.datetime.now()
h = int(now.strftime("%H"))
d = int(now.strftime("%d"))
m = int(now.strftime("%m"))
wday = int(now.weekday())
daysM = int(calendar.monthrange(now.year, now.month)[1])


def week_of_month(dt):
    """ Returns the week of the month for the specified date.
    """

    first_day = dt.replace(day=1)

    dom = dt.day
    adjusted_dom = dom + first_day.weekday()

    return int(math.ceil(adjusted_dom / 7.0))


def loadJson() -> dict:
    if not os.path.isfile("lastAct.json"):
        return {}
    f = open("lastAct.json", "r")
    o = json.loads(f.read())
    f.close()
    return o


def setJson(lastAct: dict) -> None:
    f = open("lastAct.json", "w")
    f.write(json.dumps(lastAct))
    f.close()


a = loadJson()

if "month" not in a.keys():
    a["month"] = 0

if "week" not in a.keys():
    a["week"] = 0

if "day" not in a.keys():
    a["day"] = 0

if h == 23 and d == daysM and a["month"] != m:
    tw.month()
elif wday == 6 and h == 23 and a["week"] != week_of_month(now):
    tw.week()
elif h == 23 and a["day"] != d:
    tw.day()
    tw.report()
else:
    tw.current()

setJson(a)
