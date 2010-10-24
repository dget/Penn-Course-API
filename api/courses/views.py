from django.http import HttpResponse
from models import *
from Semester import *
from APIObjects import *
import json

def JSON(x):
    return HttpResponse(json.dumps({"result": x, "valid": True, "version": "0.2"},
                                   cls=CourseObjEncoder,
                                   sort_keys=True, indent=3))

class CourseObjEncoder(json.JSONEncoder):
    def default(self, obj):
        encoders = {
            Semester: lambda s: {"code": s.code(), "name": str(s), "url": s.get_absolute_url()}
        }
        for typ, encoder in encoders.iteritems():
            if isinstance(obj, typ):
                return encoder(obj)

def index(request):
    return HttpResponse("Welcome to the PennApps Courses API!")

def root(request):
    """ display the root directory (a list of semesters) """
    min_sem, max_sem = "2010c", "2011a"
    semesters = range(Semester(min_sem).id(), Semester(max_sem).id() + 1)
    db_semesters = [semesterFromID(i) for i in semesters]
    api_semesters = [APISemester(s) for s in db_semesters]
    api_root = APIRoot()
    api_root.add_data(api_semesters)
    return JSON(api_root.encode()) 

def semester(request, semester):
    """ display all data for a semester (i.e. a list of departments) """
    db_semester = Semester(semester)
    api_semester = APISemester(db_semester)
    api_semester.add_data([APIDepartment(api_semester, d) for d in Department.objects.all()])
    return JSON(api_semester.encode())

def department(request, semester, department):
    """ display all data for a department (i.e. a list of courses) """
    db_semester = Semester(semester)
    api_semester = APISemester(db_semester)
    #todo figure out magic case-sensitivity + whitespace trimming
    db_department = Department.objects.get(code=department) 
    api_department = APIDepartment(api_semester, db_department)
    db_aliases = Alias.objects.filter(department__code=department) \
                              .filter(semester=db_semester)
    api_department.add_data([APICourse(c.course, api_semester) for c in db_aliases])
    return JSON(api_department.encode())

def alias(request, semester, department, coursenum):
    """ display all data for a course (i.e. a list of sections) """
    return course(request, alias_to_course(semester, department, coursenum))

def course(request, course_id):
    """ display all data for a course (i.e. a list of sections), given either Course or id """

    db_course = Course.objects.filter(id=course_id)[0] if not isinstance(course_id, Course) \
        else course_id

    
    db_semester = db_course.semester
    api_semester = APISemester(db_semester)
    api_course = APICourse(db_course, api_semester)

    db_sections = Section.objects.filter(course=db_course)
    api_sections = [APISection(api_course, s) for s in db_sections]

    db_aliases     = Alias.objects.filter(course=db_course)
    api_aliases   = [XAPIAlias(a.department.code, a.coursenum) for a in db_aliases]
    api_course.add_data(api_sections, api_aliases)


    return JSON(api_course.encode())

def alias_to_course(semester, department, coursenum):
    return (Alias.objects.filter(department__code=department)
                         .filter(coursenum=coursenum)
                         .filter(semester=Semester(semester)))[0].course

def section(request, section, semester=None, department=None, coursenum=None, course_id=None):
    """ display all data for a section """
    db_course = alias_to_course(semester, department, coursenum) if course_id==None else Course.objects.get(pk=course_id)
    api_semester = APISemester(db_course.semester)

    api_course = APICourse(db_course, api_semester)

    db_section = Section.objects.filter(course=db_course).filter(sectionnum=section)[0]

    api_section = APISection(api_course, db_section)
    db_professors = db_section.professors.all()
    db_meetingtimes = MeetingTime.objects.filter(section=db_section)
    api_section.add_data(api_instructors=[APIInstructor(p) for p in db_professors],
                         api_meetingtimes=[XAPIMeetingTime(t.start, t.end, t.day,
                                                           APIRoom(t.room))
                                           for t in db_meetingtimes])
    return JSON(api_section.encode())

def search(request):
    d = request.GET
    db_search = Offering.objects

    # search by semester
    # course=cis-120-001 [alternate way oof searching; sem defaults to current?]
    # description

    queries = {"dept": "course__department",
               "name": "course__coursename__icontains",
               "instructor": "professors__name__icontains",
               "building": "meetingtime__room__building__code",
               "type": "meetingtime__type",
               "day": "meetingtime__day__exact",
               "description": "course__description__icontains",
                }
    comparison_queries = {"sectionnum": "sectionnum",
                          "coursenum": "course__coursenum",
                          "start": "meetingtime__start", 
                          "end": "meetingtime__end", 
                          }
    for apikey_, djangokey_ in comparison_queries.iteritems():
        queries[apikey_] = djangokey_
        for m in ("lt", "lte", "gt", "gte"):
            queries["%s_%s" % (apikey_, m)] = "%s__%s" % (djangokey_, m)

    for apikey, djangokey in queries.iteritems():
        if apikey in d:
            db_search = eval("db_search.filter(%s=d[apikey])" % djangokey)

    n_results_start = 0
    n_results_shown = 100
    n_results_total = len(db_search.all())
    db_offerings = db_search.all()[n_results_start:n_results_start + n_results_shown]

    def make_api_section(db_offering):
        db_course = db_offering.course
        db_semester = db_offering.semester
        db_department = db_course.department

        api_semester = APISemester(db_semester)
        api_department = APIDepartment(api_semester, db_department)
        api_course = APICourse(api_department, db_course)
        api_section = APISection(api_course, db_offering)
        return api_section
    api_sections = [make_api_section(o) for o in db_offerings]
    api_results = APISearchResults(n_results_start,
                                   n_results_total, api_sections)
    return JSON(api_results.encode())

def instructor(request, instructor):
    # change to get() once professors are unique
    db_professor = Professor.objects.filter(name=instructor)[0]
    api_instructor = APIInstructor(db_professor)
    return JSON(api_instructor.encode())

def building(request, building):
    db_building = Building.objects.filter(code=building).get()
    api_building = APIBuilding(db_building)
    return JSON(api_building.encode())
