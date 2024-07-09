from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Child(models.Model):
  name = models.CharField(max_length=100)
  age = models.IntegerField()

  def __str__(self):
    return self.name

  def get_points(self, period='all'):
    end_date = timezone.now().date()
    if period == 'day':
      start_date = end_date
    elif period == 'week':
      start_date = end_date - timedelta(days=7)
    elif period == 'month':
      start_date = end_date - timedelta(days=30)
    else:  # 'all'
      start_date = None

    assignments = self.choreassignment_set.filter(completed=True)
    if start_date:
      assignments = assignments.filter(date_completed__range=[start_date, end_date])

    return sum(assignment.chore.points for assignment in assignments)

class Chore(models.Model):
  name = models.CharField(max_length=200)
  description = models.TextField(blank=True)
  points = models.IntegerField(default=1)

  def __str__(self):
    return self.name

class ChoreAssignment(models.Model):
  child = models.ForeignKey(Child, on_delete=models.CASCADE)
  chore = models.ForeignKey(Chore, on_delete=models.CASCADE)
  date_assigned = models.DateField(auto_now_add=True)
  date_completed = models.DateField(null=True, blank=True)
  completed = models.BooleanField(default=False)

  def __str__(self):
    return f"{self.child.name} - {self.chore.name}"