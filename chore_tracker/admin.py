from django.contrib import admin

from .models import Child, Chore, ChoreAssignment

admin.site.register(Child)
admin.site.register(Chore)
admin.site.register(ChoreAssignment)
