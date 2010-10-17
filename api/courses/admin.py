from courses.models import *
from django.contrib import admin

for model in ALLMODELS:
    admin.site.register(model)
