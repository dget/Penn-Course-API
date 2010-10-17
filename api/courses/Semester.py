class Semester:
    """ A semester, with a calendar year and a season.
    Season codes: (a,b,c) -> (Spring, Summer, Fall)"""
    def __init__(self, year = None, semester = None):
        """ Create a semester from a year and a season code.
            Valid inputs (all case-insensitive): Semester(2010, 'c') ==
                Semester('2010', 'c') == Semester('2010c') """
        if year is None:
            year, semester = 1740, "a" # the epoch
        if semester is None:
            year, semester = year[:-1], year[-1]
        semesternum = "abc".find(semester.lower())
        if semesternum == -1:
            raise ValueError("Invalid semester code: " + semester)
        
        self.year = int(year) # calendar year
        self.semesternum = semesternum # (0,1,2) -> (Spring, Summer, Fall)
        
    def id(self):
        """ Returns the numerical ID for this semester.
        (Year Y, semester s) (with s=0,1,2 -> a,b,c) is semester
            3(Y-1740) + s     = 780 + 3(Y-2000) + s
        Semester 2010a is 810. Current (2010c) is 812. """
        return 3*(self.year-1740) + self.semesternum
    
    def seasoncodeABC(self):
        """ Returns the season code. """
        return "abc"[self.semesternum]
    
    def code(self):
        """ Returns code YYYYa (calendar year + season code) """
        return "%4d%s" % (self.year, self.seasoncodeABC())
    
    def __repr__(self):
        return "Semester(%d,\"%s\")" % (self.year, self.seasoncodeABC())
    
    def __str__(self):
        return "%s %d" % (["Spring", "Summer", "Fall"][self.semesternum], self.year)

    def get_absolute_url(self):
        return "/courses/course/" + self.code()

    # todo: hash, comparison

def semesterFromID(id):
    """ Given a numerical semester ID, return a semester. """
    return Semester(1740 + id/3, "abc"[id % 3])


from django.db import models

class SemesterField(models.Field):
    description = "A semester during which a course may be offered"

    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        super(SemesterField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "SemesterField"

    def db_type(self, connection):
        return 'smallint'

    def to_python(self, value):
        if isinstance(value, Semester):
            return value
        if value == "":
            return Semester()
        if "HACKS!": # commence hack:
            try:
                seasons = ["Spring", "Summer", "Fall"]
                tmp_season, tmp_year = value.split(" ")
                if tmp_season in seasons:
                    return Semester(tmp_year, "abc"[seasons.index(tmp_season)])
            except: pass
	try: 
            return semesterFromID(int(value))
        except Exception as e:
            raise Exception("badness %s %s" % (value, e))

    def get_prep_value(self, value):
        return value.id()
