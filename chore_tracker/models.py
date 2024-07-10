from datetime import timedelta

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Child(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()

    def clean(self):
        if self.age < 0 or self.age > 100:
            raise ValidationError("Age must be between 0 and 100.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

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

    def __str__(self):
        return self.name


class Chore(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    points = models.IntegerField(default=1)

    def __str__(self):
        return self.name


class ChoreAssignment(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE)
    date_assigned = models.DateField(default=timezone.now)
    completed = models.BooleanField(default=False)
    date_completed = models.DateField(null=True, blank=True)

    def clean(self):
        if self.completed and not self.date_completed:
            raise ValidationError("Date completed is required when the chore is marked as completed.")
        if self.date_completed and self.date_completed < self.date_assigned:
            raise ValidationError("Date completed cannot be earlier than the date assigned.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.child.name} - {self.chore.name}"
