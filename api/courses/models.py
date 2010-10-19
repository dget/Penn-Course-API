from django.db import models
from Semester import *
import urllib

# Create your models here.

# Note: each class has get_absolute_url - this is for "url" when queried

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
    semester = SemesterField() # models.IntegerField() # ID to create a Semester
    name = models.CharField(max_length=200)
    credits = models.FloatField()
    description = models.TextField()

    def __unicode__(self):
        return "%s %s" % (self.id, self.name)

    def get_absolute_url(self):
        return "/courses/course/%d" % (self.id,)
        # don't have the actual semester

class Professor(models.Model):
    """ A course instructor or TA (or "STAFF") """
    name = models.CharField(max_length = 80) 
    
    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return "/courses/instructor/%s/" % urllib.quote(self.name) # temporary

class Alias(models.Model):
    """ A section of a course during a particular semester. """
    course = models.ForeignKey(Course)
    department = models.ForeignKey(Department)
    coursenum = models.IntegerField()
    semester = SemesterField()

    def __unicode__(self):
        return "%s: %s-%03d (%s)" % (self.course.id, self.department, self.coursenum,
                                 self.semester.code())

    def get_absolute_url(self):
        return "/courses/course/%s/%s/%03d/" % (self.semester.code(),
                                                     str(self.course.department).lower(),
                                                     self.course.coursenum)
 
class Section(models.Model):
    """ A section of a course during a particular semester. """
    course     = models.ForeignKey(Course)
    sectionnum = models.IntegerField()
    professors = models.ManyToManyField(Professor)
    group      = models.IntegerField()

    def __unicode__(self):
        return "%s-%03d " % (self.course, self.sectionnum)

    def get_absolute_url(self):
        return "/courses/course/%s/%s/%03d/%03d/" % (self.semester.code(),
                                                     str(self.course.department).lower(),
                                                     self.course.coursenum,
                                                     self.sectionnum)
    class Meta:
        """ To hold uniqueness constraint """
        unique_together = (("course", "sectionnum"),)

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
    building = models.ForeignKey(Building)
    roomnum = models.CharField(max_length=5)
    name = models.CharField(max_length=80)
    # name is empty string if room doesn't have special name
    # (e.g. Wu and Chen Auditorium), don't bother putting in "LEVH 101"

    class Meta:
        """ To hold uniqueness constraint """
        unique_together = (("building", "roomnum"),)
    def __unicode__(self):
        if self.name != "":
            return self.name
        else:
            return "%s %s" % (self.building, self.roomnum)

class MeetingTime(models.Model):
    """ A day/time/location that a class meets. """
    section = models.ForeignKey(Section)
    type = models.CharField(max_length=3)
    day = models.CharField(max_length=1)
    start = models.IntegerField()
    end = models.IntegerField()
    room = models.ForeignKey(Room)

    def __unicode__(self):
        return "%s %s - %s @ %s" % (self.day, self.start, self.end, self.room)

ALLMODELS = [Department, Alias, Course, Section, MeetingTime, Professor, Building, Room]
