#!/usr/bin/python
import re, sys, itertools
import MySQLdb, sqlite3
import datetime, time, calendar

semester = '2010C'
semesterid = 812

db=REDACTED

#db=sqlite3.connect('classes.db')

# matching days up to numbers from DB - no sundays apparently
days = { 'U': 0, 'M': 1, 'T': 2, 'W': 3, 'R': 4, 'F': 5, 'S': 6 }



def timeinfo_to_times(starttime, endtime, ampm):
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

def getRoom(room):
    if room == "TBA":
        room = "TBA 0"
    if len(room.split(' ')) != 2:
        print room 
    (building, roomnum) = room.split(' ')
    c = db.cursor()
    c.execute("""SELECT id FROM courses_building WHERE code = %s""", (building,))
    cid = c.fetchone()
    buildingid = None
    if None != cid:
        buildingid = cid[0]
    else:
        c.execute("""INSERT INTO courses_building (code, name) VALUES (%s, %s)""", (building, building))
        buildingid = db.insert_id()

    c.execute("""SELECT id FROM courses_room WHERE building_id=%s AND roomnum = %s""", (buildingid, roomnum))
    rid = c.fetchone()
    
    if None == rid: 
        c.execute("""INSERT INTO courses_room (building_id, roomnum, name) VALUES (%s, %s, %s)""", (buildingid, roomnum, ""))
        return db.insert_id()
    else:
        return rid[0]

def addTime(course, start, offeringid, c): 
    typeabbr = course['time'][start]

    days = course['time'][start+1]
    times = timeinfo_to_times(course['time'][start+2], course['time'][start+3], course['time'][start+4])

    queries = list()
    for day in days:
        queries.append((offeringid, typeabbr, day, times[0], times[1], getRoom(course['time'][start+5])))

    c.executemany("""INSERT IGNORE INTO courses_meetingtime (offering_id, type, day, start, end, room_id) VALUES (%s, %s, %s, %s, %s, %s)""", \
                  queries)


def addOffering(course):
    # create db cursor
    c=db.cursor()

    # info to add to courses table
    cname = ' '.join([x.capitalize() for x in course['name'].split(' ')])
    cdept = course['code'].split('-')[0].strip()
    cnum  = course['code'].split('-')[1]
    credits = course['credits']

    # only add if the class isn't already there.. prevents multiple sections from forming their own thing
    c.execute("""SELECT id FROM courses_course WHERE coursenum = %s AND department_id = %s AND coursename = %s""", \
                  (cnum, cdept, cname))
    cid = c.fetchone()
    if None == cid:
        c.execute("""INSERT INTO courses_course (department_id, coursenum, coursename, credits) VALUES (%s, %s, %s, %s)""", \
                  (cdept, cnum, cname, credits))
        cid = db.insert_id()
    else:
        cid = cid[0]
        
    # Add offering
    c.execute("""INSERT INTO courses_offering (course_id, sectionnum, semester) VALUES (%s, %s, %s)""", (cid, course['time'][0], semesterid))
    offeringid = db.insert_id()

    profs = []
    # Add professor(s)
    for prof in course['time'][13].split('/'):
        c.execute("""INSERT INTO courses_professor (name) VALUES (%s)""", (prof,))
        profs.append(db.insert_id())

    c.executemany("""INSERT INTO courses_offering_professors (offering_id, professor_id) VALUES (%s, %s)""", \
                      [(offeringid, prof) for prof in profs])

    
    # first insert the first time
    addTime(course, 1, offeringid, c)

    # add second time if there is one
    addTime(course, 7, offeringid, c)

    # add third time if there is one
    addTime(course, 14, offeringid, c)
 
depts = dict();
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
    # I'm sorry.
    sectionnum = r"\s+(\d{3})\s+"
    timeset = r"([A-Z]{3})\s+(\w+)\s+((?:[1-9]|10|11|12)(?:\:\d{2})?)-((?:[1-9]|10|11|12)(?:\:\d{2})?)(AM|PM|NOON)(?:\ +((?:[\w\-]+ [\w\d\-]+|TBA)))?"

    timerestring = r"^" + sectionnum + timeset + r"(?:, " + timeset +")?" + r"\ *(.*)(?:\s+" + timeset + ")?\n"

    timeregex = re.compile(timerestring, re.M)
    
    classes = itertools.chain.from_iterable([[{'code': x[1], 'name': x[2], 'credits': x[3] if "" != x[3] else x[4] if "" != x[4] else 0, 'time': t} for t in timeregex.findall(x[0])] for x in matches])

    #these fix the two-line class times
    secondtimerestring = r"^" + sectionnum + r"\ +(.+)(?:\s+" + timeset + r")?" + r"(?:, " + timeset +")?" + r"(?:\s+" + timeset + ")?\n" 
    secondtimeregex = re.compile(secondtimerestring, re.M)

    classes2 = itertools.chain.from_iterable([[{'code': x[1], 'name': x[2], 'time': t, 'credits': x[3] if "" != x[3] else x[4] if "" != x[4] else 0} for t in secondtimeregex.findall(x[0]) if t != None] for x in matches] ) 


    numcourses = 0
    dept = ""
    for z in classes:
#        print z
        dept = z['code'].split('-')[0]
        addOffering(z)
        numcourses = numcourses + 1

    for z in classes2:
        newtimes = []
        prof = z['time'][1]
        newtimes.append(z['time'][0])
        for x in range(2, len(z['time'])+1):
            if x == 14:
                newtimes.append(prof)
            elif x < 14:
                newtimes.append(z['time'][x])
            else:
                newtimes.append(z['time'][x-1])
        z['time'] = tuple(newtimes)
        numcourses = numcourses + 1
 #       print z
        addOffering(z)
    print file, numcourses
    c = db.cursor()
#    dept = "".join([x.capitalize() for x in file.split('.')[0]])
    c.execute("""INSERT IGNORE INTO courses_department (code, name) VALUES (%s, %s)""", (dept, dept))
 

