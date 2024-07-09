from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import Child, Chore, ChoreAssignment
import json

class ChoreTrackerIntegrationTests(TestCase):
  def setUp(self):
    self.client = Client()
    self.child = Child.objects.create(name="Test Child", age=10)
    self.chore = Chore.objects.create(name="Test Chore", description="Test Description", points=5)

  def test_create_child_and_assign_chore(self):
    # Create a new child
    response = self.client.post(reverse('child_create'), {'name': 'New Child', 'age': 8})
    self.assertEqual(response.status_code, 302)  # Redirect after successful creation
    new_child = Child.objects.get(name='New Child')

    # Create a new chore
    response = self.client.post(reverse('chore_create'),
                                {'name': 'New Chore', 'description': 'New Description', 'points': 3})
    self.assertEqual(response.status_code, 302)  # Redirect after successful creation
    new_chore = Chore.objects.get(name='New Chore')

    # Assign the chore to the child
    response = self.client.post(reverse('chore_assignment_create'),
                                {'child': new_child.id, 'chore': new_chore.id})
    self.assertEqual(response.status_code, 302)  # Redirect after successful creation

    # Check if the assignment exists
    self.assertTrue(ChoreAssignment.objects.filter(child=new_child, chore=new_chore).exists())

  def test_complete_chore_and_check_points(self):
    # Create a chore assignment
    assignment = ChoreAssignment.objects.create(child=self.child, chore=self.chore)

    # Complete the chore
    response = self.client.post(reverse('chore_assignment_complete', args=[assignment.id]))
    self.assertEqual(response.status_code, 302)  # Redirect after successful completion

    # Refresh the assignment from the database
    assignment.refresh_from_db()
    self.assertTrue(assignment.completed)
    self.assertIsNotNone(assignment.date_completed)

    # Check points in child detail view
    response = self.client.get(reverse('child_points', args=[self.child.id]))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, str(self.chore.points))  # The points should be displayed

  def test_calendar_view_with_completed_chores(self):
    # Complete a chore
    assignment = ChoreAssignment.objects.create(
      child=self.child,
      chore=self.chore,
      completed=True,
      date_completed=timezone.now().date()
    )

    # Check calendar view
    response = self.client.get(reverse('child_calendar', args=[self.child.id]))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, str(self.chore.points))  # The points should be displayed in the calendar

  def test_child_list_to_detail_flow(self):
    # Access the child list
    response = self.client.get(reverse('child_list'))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, self.child.name)

    # Access the child detail (points) page
    response = self.client.get(reverse('child_points', args=[self.child.id]))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, self.child.name)

  def test_create_multiple_assignments_and_complete(self):
    # Create multiple chores
    chore2 = Chore.objects.create(name="Test Chore 2", description="Test Description 2", points=3)
    chore3 = Chore.objects.create(name="Test Chore 3", description="Test Description 3", points=7)

    # Assign all chores to the child
    for chore in [self.chore, chore2, chore3]:
      ChoreAssignment.objects.create(child=self.child, chore=chore)

    # Complete all chores
    for assignment in ChoreAssignment.objects.filter(child=self.child):
      response = self.client.post(reverse('chore_assignment_complete', args=[assignment.id]))
      self.assertEqual(response.status_code, 302)

    # Check total points
    response = self.client.get(reverse('child_points', args=[self.child.id]))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, str(self.chore.points + chore2.points + chore3.points))



