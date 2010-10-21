#!/usr/bin/python

# Imports fail? Try:
# export DJANGO_SETTINGS_MODULE=api.settings
# export PYTHONPATH=$(cd ..;pwd)

import re, sys, itertools
import datetime, time, calendar
from api import settings, courses

from api.courses.models import *

year   = '2011'
season = 'a'
timetable = True # true if there's no rooms yet

def timeinfo_to_times(starttime, endtime, ampm):
    """ Takes a start and end time, along with am/pm, returns an integer (i.e., 1200 for noon) """
    #first, split each time into list with hours as first element, minutes maybe as second

    startlist = starttime.split(':')
    endlist   = endtime.split(':')
        
    if ('PM' == ampm):
        endlist[0] = str(int(endlist[0])+12)
        # if it's pm, and start time is before 8, make it a pm.. ex. 1-3PM should be 1PM-3PM
        if (int(startlist[0]) <= 8):
            startlist[0] = str(int(startlist[0]) + 12)
            
    if (1 == len(startlist)):
        startlist.append('00')
        
    if (1 == len(endlist)):
        endlist.append('00')
    

    finalstart = int(''.join(startlist))
    finalend = int(''.join(endlist))
    
    return (finalstart, finalend)

def removeFirstLine(string):
    """ Returns everything after the first newline in a string """
    pos = string.find('\n') + 1
    return string[pos:]

def divideGroups(text):
    """ Divide text about different groups """
    return re.split('GROUP \d+ SECTIONS\n', text)

def findTimes(text):
    sectionnum = r"\s+(\d{3})\s+"
    timeset = r"([A-Z]{3})\s+(\w+)\s+((?:[1-9]|10|11|12)(?:\:\d{2})?)-((?:[1-9]|10|11|12)(?:\:\d{2})?)(AM|PM|NOON)(?:\ +((?:[\w\-]+ [\w\d\-]+|TBA)))?"
    timerestring = r"^" + sectionnum + timeset + r"(?:, " + timeset +")?" + r"\ *(.*)(?:\s+" + timeset + ")?\n"
    timeregex = re.compile(timerestring, re.M)
    
    # this fixes two-lines class times
    secondtimerestring = r"^" + sectionnum + r"\ +(.+)(?:\s+" + timeset + r")?" + r"(?:, " + timeset +")?" + r"(?:\s+" + timeset + ")?\n" 
    secondtimeregex = re.compile(secondtimerestring, re.M)

    times1 = timeregex.findall(text)
    
    times = [parseTime(x) for x in times1]

    times2 = [parseTime(x, True) for x in secondtimeregex.findall(text)]
    times.extend(times2)

    return times

def parseTime(timeTuple, earlyInstructor=False):
    """ Converts massive tuple that findTimes regexi return into something
        moderately useful. earlyInstructor is true if instructor's the
        second item in the tuple, false if 14th. """

    # early instructor case for timetable
    if timetable and timeTuple[6] != '':
        earlyInstructor = True
    instructor = ((timeTuple[6] if timetable else timeTuple[1]) 
                  if earlyInstructor else timeTuple[13])
    print timeTuple
    x = { 'num'        : timeTuple[0],
          'instructor' : instructor,
          'meetings'   : []}

    # Deal with potentially multiple meeting times
    timeStart = 2 if earlyInstructor and not timetable else 1
    length = 5 if timetable == True else 6 # there's no room if a timetable
    if timeTuple[timeStart] != '':
        x['meetings'].append(timeTuple[timeStart:timeStart+length])
    if timeTuple[timeStart+6] != '':
        x['meetings'].append(timeTuple[timeStart+6:timeStart+6+length])
    if timeTuple[14] != '':
        x['meetings'].append(timeTuple[14:])
    
    return x

def djangoize(time):
    sem = Semester(year, season)
    if False == verifyAlias(time['code'], time['crosslists']):
        return
    course = Course()
    course.name     = time['name']
    course.credits  = time['credits']
    course.semester = sem
    course.save()
    saveAlias(time['code'], time['crosslists'], course)
    saveSections(time['groups'], course)
    print time

def verifyAlias(code, crosslists):
    """ True if the given alias doesn't already exist, false otherwise """
    crosslists.append(code)
    for x in crosslists:
        (deptString, num) = x.split('-')
        try:
            dept = Department.objects.filter(code=deptString.strip())[0]
        except IndexError:
            continue
        obj = Alias.objects.filter(department=dept, 
                                   coursenum=num.strip(), 
                                   semester=Semester(year, season))
        if len(obj) > 0:
            return False
    return True

    
def saveAlias(code, crosslists, course):
    """ This will save the alias for a given course, given a code (such as CIS-110 and the course object """

    sem = Semester(year, season)

    for cross in crosslists:
        alias = Alias()
        alias.course = course
        (deptString, num) = cross.split('-')
        # Assumes department exists already
        try:
            dept = Department.objects.filter(code=deptString.strip())[0]
        except IndexError:
            dept = Department()
            dept.code = deptString.strip()
            dept.name = deptString.strip()
            dept.save()
        alias.department = dept
        alias.coursenum  = num.strip()
        alias.semester   = sem
        alias.save()

def saveSections(groups, course):
    for groupnum, group in enumerate(groups):
        for sectInfo in group:
            section = Section()
            section.course     = course
            section.sectionnum = sectInfo['num']
            section.group = groupnum
            section.save()
            for prof in sectInfo['instructor'].split('/'):
                section.professors.add(saveProfessor(sectInfo['instructor']))
            section.save()

            for meeting in sectInfo['meetings']:
                for day in meeting[1]:
                    time = MeetingTime()
                    time.section = section
                    time.type    = meeting[0]
                    time.day     = day
                    (start, end) = timeinfo_to_times(meeting[2],
                                                     meeting[3],
                                                     meeting[4])
                    time.start   = start
                    time.end     = end
                    time.room    = saveRoom(meeting[5] if len(meeting) > 5
                                                       else "TBA")
                    time.save()


def saveProfessor(name):
    """ Returns a Professor given a name, creating if necessary """
    prof = Professor()
    prof.name = name
    prof.save()
    return prof

def saveRoom(roomCode):
    """ Returns a Room given code, creating room and building if necessary """

    # This is wrong.
    if "TBA" == roomCode or "" == roomCode:
        roomCode = "TBA 0"

    (buildCode, roomNum) = roomCode.split(' ')

    # try finding a building, if nothing, return a new one
    try:
        building = Building.objects.filter(code=buildCode)[0]
    except IndexError:
        building = Building()
        building.code = buildCode
        building.name = ''
        building.latitude = 0.0
        building.longitude = 0.0
        building.save()

    # try finding the room, if nothing return a new one
    try:
        room = Room.objects.filter(building=building).filter(roomnum=roomNum)[0]
    except IndexError:
        room = Room()
        room.building = building
        room.roomnum  = roomNum
        room.name= ''
        room.save()
    return room

def findCrossLists(text):
    crosslist_start = r"CROSS LISTED: "
    crosslist_end   = r"SECTION MAX"
    restring = crosslist_start + r"(?:(\w{2,5}\s?\s?-\d{3}).*?)" + crosslist_end
    regex = re.compile(restring, re.M)
    return regex.findall(text)

for file in sys.argv:
    if 'printcourses.py' == file:
        continue
    if '' == file:
        continue
    f = open('%s' % file)
    
    #record subject name to be added later
    subjname = f.readline().strip()

    # this is line one of a class
    restring = r"^((\w{2,5}\s?\s?-\d{3})\s+(\w+.*?)\s+(?:(\d) CU|\d TO \d CU|(\d\.\d) CU)\n(.+\n)+?\s*\n)"
    regex = re.compile(restring, re.M)
    filestr = f.read()
    matches = regex.findall(filestr)
    
    
    matches = [{'code'   : x[1], 
                'name'   : x[2], 
                'credits': x[3] if "" != x[3] else x[4] if "" != x[4] else 0,
                'groups' : [findTimes(t) for t in divideGroups(removeFirstLine(x[0]))],
                'crosslists': findCrossLists(removeFirstLine(x[0]))
                } for x in matches]

    for x in matches:
        djangoize(x)

