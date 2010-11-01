#!/usr/bin/python

# Imports fail? Try:
# export DJANGO_SETTINGS_MODULE=api.settings
# export PYTHONPATH=$(cd ..;pwd)

import re, sys, itertools
import datetime, time, calendar, pprint
from api import settings, courses

from api.courses.models import *

year   = '2011'
season = 'a'
timetable = True # true if there's no rooms yet
class Importer(object):
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

    def verifyAlias(self, code, crosslists):
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


    def importDepartment(self, dept):
        deptname = dept[0]
        courses = dept[1]
        for c in courses:
            self.importCourse(c)

    def importCourse(self, course):
        print course
        # sem = Semester(year, season)
        # if False == verifyAlias(time['code'], time['crosslists']):
        #     return
        # course = Course()
        # course.name     = time['name']
        # course.credits  = time['credits']
        # course.semester = sem
        # course.save()
        # saveAlias(time['code'], time['crosslists'], course)
        # saveSections(time['groups'], course)

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


class Parser(object):
    def removeFirstLine(self, string):
        """ Returns everything after the first newline in a string """
        pos = string.find('\n') + 1
        return string[pos:]

    def divideGroups(self, text):
        """ Divide text about different groups """
        return re.split('GROUP \d+ SECTIONS\n', text)

    def findTimes(self, section, timetable = True):
        room = r"((?:[\w\-]+ [\w\d\-]+|TBA))"
        timeset = r"([A-Z]{3})\s+(\w+)\s+((?:[1-9]|10|11|12)(?:\:\d{2})?)-((?:[1-9]|10|11|12)(?:\:\d{2})?)(AM|PM|NOON)(?:\ +" + \
            (room if not timetable else r"") + r")?"

        time_regex = re.compile(timeset, re.M)
        return [self.parseTime(x) for x in time_regex.findall(section)]

    def findCrossLists(self, text):
        crosslist_start = r"(?:CROSS LISTED|CROSS-LISTED): "
        crosslist_end   = r"SECTION MAX"
        restring = crosslist_start + r"(?:(\w{2,5}\s?\s?-\d{3}).*?)" + crosslist_end
        regex = re.compile(restring, re.M)
        return regex.findall(text)

    def findSections(self, course):
        time_regex = r"^ (?:(\d{3}) (.*))"
        time_re = re.compile(time_regex, re.M)
        sections =  list(time_re.finditer(course)) # match objects for each section
        
        sect_combos = zip(sections, sections[1:]) # match the start of each section up with start of next

        return [course] if len(sect_combos)==0 else [course[x.start(0):y.start(0)] for x, y in sect_combos if course[x.start(0):y.start(0)].strip() != ""]

    def findInstructor(self, section):
        pattern = r" \d{3} .*?(?:AM|PM|NOON|TBA) (.*)"
        match = re.compile(pattern).search(section)
        if None == match:
            return None
        else:
            return match.group(1).strip()

    def findId(self, section):
        pattern = r"^ (\d{3})"
        match = re.compile(pattern).search(section)
        if None == match:
            return None
        return match.group(1).strip()

    def parseDepartment(self, f):
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
                    'groups' : p.divideGroups(p.removeFirstLine(x[0])),
                    'crosslists': p.findCrossLists(p.removeFirstLine(x[0])),
                    'remaining' : p.removeFirstLine(x[0])
                    } for x in matches]

        for match in matches:
            sectGroups  = [p.findSections(g) for g in match['groups']]

            sections = [[{'instructor': p.findInstructor(s), 
                          'times':      p.findTimes(s), 
                          'id':         p.findId(s)} for s in g] for g in sectGroups]
            match['sections'] = sections
            del match['remaining']
            del match['groups']
        return (subjname, matches)


for file in sys.argv:
    if 'printcourses.py' == file:
        continue
    if '' == file:
        continue
    f = open('%s' % file)

    p = Parser()

    x = p.parseDepartment(f)
    
    i = Importer()
    i.importDepartment(x)

#    pp = pprint.PrettyPrinter(indent=4)
#    pp.pprint(x)
    
