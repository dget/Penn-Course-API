from django.db import models
from Semester import *
import urllib

# Create your models here.

class Department(models.Model):
    """A department/subject"""
    code = models.CharField(max_length=5, primary_key=True)
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.code

    def get_absolute_url(self):
        return "/courses/course/current/%s/" % self.code.lower() # don't know actual semester

class Course(models.Model):
    """A course that can be taken (e.g. CIS 120).
       Does not contain any time information.

       The following pairs are pairs of distinct courses,
         but should probably be associated in some other table:
       CIS 160 and CIS 260 (they are numbered differently)
       CIS 120 and CSE 120 (numbered differently)
       COGS 001 and CIS 140 [crosslisted] (numbered differently)
       WRIT 039 301 and WRIT 039 303 (they have same course number,
          but different titles)
    """
    department = models.ForeignKey(Department)
    coursenum = models.IntegerField()
    coursename = models.CharField(max_length=200)
    credits = models.FloatField()
    description = models.TextField()

    def __unicode__(self):
        return "%s %03d" % (self.department, self.coursenum)

    def get_absolute_url(self):
        return "/courses/course/current/%s/%03d/" % (str(self.department).lower(), self.coursenum)
        # don't have the actual semester

class Professor(models.Model):
    """ A course instructor or TA (or "STAFF") """
    name = models.CharField(max_length = 80) 
    
    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return "/courses/instructor/%s/" % urllib.quote(self.name) # temporary

class Offering(models.Model):
    """ A section of a course during a particular semester. """
    course = models.ForeignKey(Course)
    sectionnum = models.IntegerField()
    semester = SemesterField() # models.IntegerField() # ID to create a Semester
    professors = models.ManyToManyField(Professor)

    def __unicode__(self):
        return "%s-%03d (%s)" % (self.course, self.sectionnum,
                                 self.semester.code())

    def get_absolute_url(self):
        return "/courses/course/%s/%s/%03d/%03d/" % (self.semester.code(),
                                                     str(self.course.department).lower(),
                                                     self.course.coursenum,
                                                     self.sectionnum)
 
class Building(models.Model):
    """ A building at Penn. """
    code = models.CharField(max_length=4)
    name = models.CharField(max_length=80)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __unicode__(self):
        return self.code

    def get_absolute_url(self):
        return "/courses/building/%s/" % self.code.lower()

class Room(models.Model):
    """ A room in a building. It optionally may be named. """
    building = models.ForeignKey(Building, unique = True)
    roomnum = models.CharField(max_length=5, unique = True)
    name = models.CharField(max_length=80, unique = True)
    # name is empty string if room doesn't have special name
    # (e.g. Wu and Chen Auditorium), don't bother putting in "LEVH 101"

    def __unicode__(self):
        if self.name != "":
            return self.name
        else:
            return "%s %s" % (self.building, self.roomnum)

class MeetingTime(models.Model):
    """ A day/time/location that a class meets. """
    offering = models.ForeignKey(Offering)
    type = models.CharField(max_length=3)
    day = models.CharField(max_length=1)
    start = models.IntegerField()
    end = models.IntegerField()
    room = models.ForeignKey(Room)

    def __unicode__(self):
        return "%s %s - %s @ %s" % (self.day, self.start, self.end, self.room)

ALLMODELS = [Department, Course, Professor, Offering, Building, Room, MeetingTime]
