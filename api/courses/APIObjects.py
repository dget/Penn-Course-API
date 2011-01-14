import urllib

""" 
Naming convention:
  db_* - a Model (or other database-tied obj, e.g. Semester)
  api_* - an APIObject, probably a reference (i.e. not fully formed)       

"""

class APIObjectUninitializedError(Exception):
    """ Uninitialized APIObject cannot be encoded """
    pass

class APIObject:
    """ An object returned by the API, which can be converted to a JSON-
    serializable object. Additional data (provided with add_data()) may be required
    for the encode() method; if this is not set, encode() will fail. However,
    encode_refr() should always work even if these parameters are not set."""

    def __init__(self):
        self.initialized = False # this still doesn't work

    def encode_refr(self):
        """ returns a JSON serializable object representing
        a reference to the object (including a link where more
        information can be obtained if necessary. This method should
        succeed, even if the object is not fully initialized. """
        
	d = self.api_refr_data()
	d["id"] = self.api_id()
	d["name"] = self.api_name()
	d["url"] = self.api_url()
	return d

    def encode(self):
        """ returns a JSON-serializible object representing the full state of the object.
            throws APIObjectUninitializedError if not fully initialized. """
        if not self.initialized:
            raise APIObjectUninitializedError()
        d = self.api_data()
        d["id"] = self.api_id()
        d["name"] = self.api_name()
        return d

    def api_id(self):   raise NotImplementedError()
    def api_name(self): raise NotImplementedError()
    def api_url(self):  raise NotImplementedError()
    def api_data(self): raise NotImplementedError()
    def api_refr_data(self):  return {}

class APIRoot(APIObject):
    def __init__(self): pass
    def add_data(self, api_semesters):
        self.api_semesters = api_semesters
        self.initialized = True

    def api_id(self):   return "upenn"
    def api_name(self): return "University of Pennsylvania"
    def api_url(self):  return "/courses/course/"

    def api_data(self):
        return {"semesters": [s.encode_refr() for s in self.api_semesters] }

class APISemester(APIObject):
    """ A semester, as returned by the API.
    Stores a db Semester object and a list of APIDepartment references. """
    def __init__(self, db_semester):
        self.db_semester = db_semester
    def add_data(self, api_depts):
        self.api_depts = api_depts
        self.initialized = True

    def api_id(self):
        return self.db_semester.code() # "2010c"
    def api_name(self):
        return str(self.db_semester) # return "Fall 2010"
    def api_url(self):
        return "/courses/course/%s/" % self.api_id() # "/courses/course/2010c/"

    def api_data(self):
        return {"departments": [d.encode_refr() for d in self.api_depts] }

class APIDepartment(APIObject):
    def __init__(self, api_semester, db_department):
        self.api_semester = api_semester
        self.db_department = db_department
    def add_data(self, api_courses):
        self.api_courses = api_courses
        self.initialized = True

    def api_id(self):
        return self.db_department.code.strip() # "CIS"
    def api_name(self):
        return self.db_department.name # "Computer and Information Science"
    def api_url(self):
        return "%s%s/" % (self.api_semester.api_url(), self.api_id().lower())

    def api_data(self):
        return {"semester": self.api_semester.encode_refr(),
                "courses": [c.encode_refr() for c in self.api_courses] }

class APICourse(APIObject):
    def __init__(self, db_course, api_semester, xapi_aliases):
        self.api_semester = api_semester
        self.db_course = db_course
        self.xapi_aliases = xapi_aliases
    def add_data(self, api_sections):
        self.api_sections  = api_sections
        self.initialized = True

    def api_id(self):
        return str(self.db_course.id) # "12345"

    def api_name(self):
        return ' '.join([w.capitalize() for w in self.db_course.name.split(' ')]) # "Programming Languages and Techniques I"
    def api_url(self):
        return "/courses/course/%s/" % (str(self.db_course.id))

    def api_refr_data(self):
        # TODO: sort ordering based on context (e.g. in CIS dept, put CIS aliases first)
	return {"aliases": sorted(a.api_id() for a in self.xapi_aliases)}

    def api_data(self):
        return {"aliases": [a.encode() for a in self.xapi_aliases],
                "description": self.db_course.description,
                "credits": self.db_course.credits,
                "sections": [s.encode_refr() for s in self.api_sections] }

# only need parent object

class APISection(APIObject):
    def __init__(self, api_course, db_section):
        self.api_semester = api_course.api_semester
        self.api_course = api_course
        self.db_section = db_section
    def add_data(self, api_instructors, api_meetingtimes):
        self.api_instructors = api_instructors
        self.api_meetingtimes = api_meetingtimes
        self.initialized = True

    def sectionnum_str(self):
        return "%03d" % self.db_section.sectionnum

    def api_id(self):
        return "%s-%s" % (self.api_course.api_id(), self.sectionnum_str()) # "12345-001"
    def api_name(self):
        return self.api_course.api_name() # "Programming Languages and Techniques I"
    def api_url(self):
        return "%s%s/" % (self.api_course.api_url(), self.sectionnum_str())

    def api_refr_data(self):
	return {"sectionnum": self.sectionnum_str(),
	        "group": self.db_section.group}

    def api_data(self):
        return {"course": self.api_course.encode_refr(),
                "sectionnum": self.sectionnum_str(),
                "semester": self.api_semester.encode_refr(),
                "meetingtimes": [i.encode() for i in self.api_meetingtimes],
                "instructors": [i.encode_refr() for i in self.api_instructors],
                "group": self.db_section.group}

class XAPIAlias:
    # NOT an APIObject (yet), but does have an encode() method

    def __init__(self, dept, num):
        self.dept = dept #string
        self.num  = num  #integer

    def api_id(self):
        return "%s-%03d" % (self.dept, self.num) # "CIS-120"

    def encode(self):
        return { "code": self.api_id() }


def decode_time(time_int):
    return "%02d:%02d" % (time_int / 100, time_int % 100)

class XAPIMeetingTime:
    # NOT an APIObject (yet), but does have an encode() method

    def __init__(self, start, end, day, meeting_type, room):
        self.start = start #integer
        self.end = end #integer
        self.day = day #one-char string 
        self.type = meeting_type
        self.room = room # APIRoom

    def encode(self):
        return {"start": decode_time(self.start),
                "end": decode_time(self.end),
                "day": self.day,
                "type": self.type,
                "room": self.room.encode() }

class APIBuilding(APIObject):
    def __init__(self, db_building):
        self.initialized = True
        self.db_building = db_building

    def api_id(self):
        return self.db_building.code
    def api_name(self):
        return self.db_building.name
    def api_url(self):
        return "/courses/building/%s/" % self.api_id()

    def api_data(self):
        return {"latitude": self.db_building.latitude,
                "longitude": self.db_building.longitude }

class APIRoom(APIObject):
    def __init__(self, db_room):
        self.initialized = True
        self.db_room = db_room
        self.api_building = APIBuilding(db_room.building) # todo cache api objects

    def api_id(self):
        return "%s %s" % (self.db_room.building, self.db_room.roomnum)
    def api_name(self):
        return str(self.db_room)
    def api_url(self): # todo reference apibuilding?
        return "%s%s/" % (self.api_building.api_url(), 
                          urllib.quote(self.db_room.roomnum))

    def api_data(self):
        return {"building": self.api_building.encode_refr(),
                "number": self.db_room.roomnum }
        

class APIInstructor(APIObject):
    def __init__(self, db_professor):
        self.initialized = True
        self.db_professor = db_professor
    
    def api_id(self):
        return self.api_name()
    def api_name(self):
        return self.db_professor.name
    def api_url(self):
        return "/courses/instructor/%s/" % urllib.quote(self.api_name()) # temporary

    def api_data(self):
        return {}


class APISearchResults(APIObject):
    def __init__(self, n_results_start, n_results_total, api_offerings):
        self.n_results_start = n_results_start
        self.n_results_total = n_results_total
        self.api_offerings = api_offerings
        self.initialized = True

    def api_id(self): return "search"
    def api_name(self): return "Search Results"
    def api_url(self): return "/courses/search"

    def api_data(self):
        return {"results": [o.encode_refr() for o in self.api_offerings], 
                "num_results_total": self.n_results_total,
                "num_results_shown": len(self.api_offerings), 
                "start": self. n_results_start}
