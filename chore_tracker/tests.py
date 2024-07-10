from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from .forms import ChildForm, ChoreForm, ChoreAssignmentForm
from .models import Child, Chore, ChoreAssignment


class ModelTests(TestCase):
    def setUp(self):
        self.child = Child.objects.create(name="Test Child", age=10)
        self.chore = Chore.objects.create(name="Test Chore", description="Test Description", points=5)

    def test_child_creation(self):
        self.assertEqual(self.child.name, "Test Child")
        self.assertEqual(self.child.age, 10)

    def test_chore_creation(self):
        self.assertEqual(self.chore.name, "Test Chore")
        self.assertEqual(self.chore.points, 5)

    def test_chore_assignment_creation(self):
        assignment = ChoreAssignment.objects.create(child=self.child, chore=self.chore)
        self.assertEqual(assignment.child, self.child)
        self.assertEqual(assignment.chore, self.chore)
        self.assertFalse(assignment.completed)

    def test_child_get_points(self):
        ChoreAssignment.objects.create(
            child=self.child,
            chore=self.chore,
            completed=True,
            date_completed=timezone.now().date()
        )
        self.assertEqual(self.child.get_points(period='day'), 5)
        self.assertEqual(self.child.get_points(period='week'), 5)
        self.assertEqual(self.child.get_points(period='month'), 5)
        self.assertEqual(self.child.get_points(period='all'), 5)

        # Test points for different periods
        ChoreAssignment.objects.create(
            child=self.child,
            chore=self.chore,
            completed=True,
            date_completed=timezone.now().date() - timedelta(days=10)
        )
        self.assertEqual(self.child.get_points(period='day'), 5)
        self.assertEqual(self.child.get_points(period='week'), 5)
        self.assertEqual(self.child.get_points(period='month'), 10)
        self.assertEqual(self.child.get_points(period='all'), 10)


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.child = Child.objects.create(name="Test Child", age=10)
        self.chore = Chore.objects.create(name="Test Chore", description="Test Description", points=5)

    def test_child_list_view(self):
        response = self.client.get(reverse('child_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Child")

    def test_chore_list_view(self):
        response = self.client.get(reverse('chore_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Chore")

    def test_child_create_view(self):
        response = self.client.post(reverse('child_create'), {'name': 'New Child', 'age': 8})
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertTrue(Child.objects.filter(name='New Child').exists())

    def test_chore_create_view(self):
        response = self.client.post(reverse('chore_create'),
                                    {'name': 'New Chore', 'description': 'New Description', 'points': 3})
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertTrue(Chore.objects.filter(name='New Chore').exists())

    def test_chore_assignment_create_view(self):
        response = self.client.post(reverse('chore_assignment_create'),
                                    {'child': self.child.id, 'chore': self.chore.id})
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertTrue(ChoreAssignment.objects.filter(child=self.child, chore=self.chore).exists())

    def test_child_points_view(self):
        ChoreAssignment.objects.create(
            child=self.child,
            chore=self.chore,
            completed=True,
            date_completed=timezone.now().date()
        )
        response = self.client.get(reverse('child_points', args=[self.child.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "5")  # The point value of the completed chore

    def test_calendar_view(self):
        response = self.client.get(reverse('child_calendar', args=[self.child.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.child.name)
        self.assertContains(response, timezone.now().strftime("%B %Y"))  # Current month and year


class FormTests(TestCase):
    def setUp(self):
        self.child = Child.objects.create(name="Test Child", age=10)
        self.chore = Chore.objects.create(name="Test Chore", description="Test Description", points=5)

    def test_child_form_valid(self):
        form = ChildForm(data={'name': 'New Child', 'age': 8})
        self.assertTrue(form.is_valid())

    def test_child_form_invalid(self):
        form = ChildForm(data={'name': '', 'age': 'not a number'})
        self.assertFalse(form.is_valid())

    def test_chore_form_valid(self):
        form = ChoreForm(data={'name': 'New Chore', 'description': 'New Description', 'points': 3})
        self.assertTrue(form.is_valid())

    def test_chore_form_invalid(self):
        form = ChoreForm(data={'name': '', 'description': 'New Description', 'points': 'not a number'})
        self.assertFalse(form.is_valid())

    def test_chore_assignment_form_valid(self):
        form = ChoreAssignmentForm(data={'child': self.child.id, 'chore': self.chore.id})
        self.assertTrue(form.is_valid())

    def test_chore_assignment_form_invalid(self):
        form = ChoreAssignmentForm(data={'child': '', 'chore': ''})
        self.assertFalse(form.is_valid())
