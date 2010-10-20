from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

root_pat = r'^courses/course/'
semester_pat = root_pat + r'(?P<semester>[^/]*)/'
department_pat = semester_pat + r'(?P<department>[^/]*)/'
alias_pat = department_pat + r'(?P<coursenum>[^/]*)/'
section_alias_pat = alias_pat + r'(?P<section>[^/]*)/'

# for a course's unique id
course_pat = root_pat + r'(?P<course_id>\d+)/'
section_course_pat = course_pat + r'(?P<section>[^/]*)/'

search_pat = r'^courses/search/'
instructor_pat = r'^courses/instructor/(?P<instructor>[^/]*)/'
building_pat = r'^courses/building/(?P<building>[^/]*)/'

urlpatterns = patterns('',
    # Example:
    (r'^courses/$', 'courses.views.index'),
    (root_pat           + '$', 'courses.views.root'),
    (course_pat         + '$', 'courses.views.course'),
    (section_course_pat + '$', 'courses.views.section'),
    (semester_pat       + '$', 'courses.views.semester'),
    (department_pat     + '$', 'courses.views.department'),
    (alias_pat          + '$', 'courses.views.alias'),
    (section_alias_pat  + '$', 'courses.views.section'),


    (search_pat      + '$', 'courses.views.search'),
    (instructor_pat  + '$', 'courses.views.instructor'),
    (building_pat    + '$', 'courses.views.building'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
