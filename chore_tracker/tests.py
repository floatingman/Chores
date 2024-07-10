import json
from datetime import timedelta

import factory
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from factory.django import DjangoModelFactory

from .forms import ChoreAssignmentForm
from .models import Child, Chore, ChoreAssignment


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')


class ChildFactory(DjangoModelFactory):
    class Meta:
        model = Child

    name = factory.Sequence(lambda n: f'Child {n}')
    age = factory.Faker('random_int', min=5, max=15)


class ChoreFactory(DjangoModelFactory):
    class Meta:
        model = Chore

    name = factory.Sequence(lambda n: f'Chore {n}')
    description = factory.Faker('sentence')
    points = factory.Faker('random_int', min=1, max=10)


class ChoreAssignmentFactory(DjangoModelFactory):
    class Meta:
        model = ChoreAssignment

    child = factory.SubFactory(ChildFactory)
    chore = factory.SubFactory(ChoreFactory)
    date_assigned = factory.LazyFunction(timezone.now)
    completed = False


class ChildModelTests(TestCase):
    def setUp(self):
        self.child = Child.objects.create(name="Test Child", age=10)
        self.chore1 = Chore.objects.create(name="Chore 1", points=5)
        self.chore2 = Chore.objects.create(name="Chore 2", points=10)

    def test_get_points(self):
        # Create some completed chore assignments
        ChoreAssignment.objects.create(
            child=self.child,
            chore=self.chore1,
            completed=True,
            date_completed=timezone.now().date()
        )
        ChoreAssignment.objects.create(
            child=self.child,
            chore=self.chore2,
            completed=True,
            date_assigned=timezone.now().date() - timedelta(days=4),
            date_completed=timezone.now().date() - timedelta(days=2)
        )
        ChoreAssignment.objects.create(
            child=self.child,
            chore=self.chore1,
            completed=True,
            date_assigned=timezone.now().date() - timedelta(days=12),
            date_completed=timezone.now().date() - timedelta(days=10)
        )

        self.assertEqual(self.child.get_points(period='day'), 5)
        self.assertEqual(self.child.get_points(period='week'), 15)
        self.assertEqual(self.child.get_points(period='month'), 20)
        self.assertEqual(self.child.get_points(period='all'), 20)

    def test_get_points_with_uncompleted_chores(self):
        # Create an uncompleted chore assignment
        ChoreAssignment.objects.create(
            child=self.child,
            chore=self.chore1,
            completed=False,
            date_completed=None
        )

        self.assertEqual(self.child.get_points(period='all'), 0)


class ChoreAssignmentTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password='testpass123')
        self.child1 = ChildFactory()
        self.child2 = ChildFactory()
        self.child = Child.objects.create(name="Test Child", age=10)
        self.chore = Chore.objects.create(name="Test Chore", description="Test Description", points=5)
        self.chore1 = ChoreFactory()
        self.chore2 = ChoreFactory()
        self.assignment1 = ChoreAssignmentFactory(child=self.child1, chore=self.chore1)
        self.assignment2 = ChoreAssignmentFactory(
            child=self.child2,
            chore=self.chore2,
            date_assigned=timezone.now() - timezone.timedelta(days=1),
            completed=True,
            date_completed=timezone.now()
        )

    def test_chore_assignment_list_view(self):
        """Test that the chore assignment list view displays all assignments."""
        response = self.client.get(reverse('chore_assignment_list'))
        self.assertEqual(response.status_code, 200, "Should return 200 OK.")
        self.assertContains(response, self.chore1.name, msg_prefix="Chore 1 should be in the response")
        self.assertContains(response, self.chore2.name, msg_prefix="Chore 2 should be in the response")
        self.assertTemplateUsed(response, 'chore_tracker/chore_assignment_list.html')

    def test_chore_assignment_ordering(self):
        """Test that chore assignments can be ordered correctly."""
        orderings = [
            ('-date_assigned', self.assignment1),
            ('child_name', self.assignment1 if self.child1.name < self.child2.name else self.assignment2),
            ('completed', self.assignment1),  # False comes before True
        ]
        for order_param, expected_first in orderings:
            with self.subTest(order_param=order_param):
                response = self.client.get(reverse('chore_assignment_list') + f'?order_by={order_param}')
                self.assertEqual(response.status_code, 200, f"Should return 200 OK for ordering {order_param}")
                assignments = list(response.context['chore_assignments'])
                self.assertEqual(assignments[0], expected_first,
                                 f"First assignment should be {expected_first} when ordering by {order_param}")

    def test_chore_assignment_create_view(self):
        """Test creating a new chore assignment."""
        chore_count = ChoreAssignment.objects.count()
        response = self.client.post(reverse('chore_assignment_create'), {
            'child': self.child1.id,
            'chore': self.chore2.id,
            'date_assigned': timezone.now().date(),
        })
        self.assertEqual(response.status_code, 302, "Should redirect after successful creation")
        self.assertEqual(ChoreAssignment.objects.count(), chore_count + 1, "Should create a new chore assignment")

    def test_chore_assignment_create_view_invalid_data(self):
        """Test creating a chore assignment with invalid data."""
        response = self.client.post(reverse('chore_assignment_create'), {
            'child': self.child1.id,
            # Missing 'chore' field
            'date_assigned': '2023-01-01',
        })
        self.assertEqual(response.status_code, 200, "Should return to the form on invalid data")
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('chore', response.context['form'].errors)

    def test_chore_assignment_update_view(self):
        """Test updating an existing chore assignment."""
        response = self.client.post(reverse('chore_assignment_edit', args=[self.assignment1.id]), {
            'child': self.child2.id,
            'chore': self.chore1.id,
            'date_assigned': timezone.now().date(),
            'completed': True,
            'date_completed': timezone.now().date(),
        })
        self.assertEqual(response.status_code, 302, "Should redirect after successful update")
        self.assignment1.refresh_from_db()
        self.assertEqual(self.assignment1.child, self.child2, "Child should be updated")
        self.assertTrue(self.assignment1.completed, "Assignment should be marked as completed")

    def test_chore_assignment_delete_view(self):
        """Test deleting a chore assignment."""
        chore_count = ChoreAssignment.objects.count()
        response = self.client.post(reverse('chore_assignment_delete', args=[self.assignment1.id]))
        self.assertEqual(response.status_code, 302, "Should redirect after successful deletion")
        self.assertEqual(ChoreAssignment.objects.count(), chore_count - 1, "Should delete the chore assignment")

    def test_chore_assignment_complete_view(self):
        """Test marking a chore assignment as complete."""
        response = self.client.post(reverse('chore_assignment_complete', args=[self.assignment1.id]))
        self.assertEqual(response.status_code, 302, "Should redirect after marking as complete")
        self.assignment1.refresh_from_db()
        self.assertTrue(self.assignment1.completed, "Assignment should be marked as completed")
        self.assertIsNotNone(self.assignment1.date_completed, "Completion date should be set")

    def test_chore_assignment_form_validation(self):
        """Test custom validation in the ChoreAssignmentForm."""
        # Test that date_completed is required if completed is True
        form = ChoreAssignmentForm(data={
            'child': self.child.id,
            'chore': self.chore.id,
            'date_assigned': timezone.now().date(),
            'completed': True,
            # Missing date_completed
        })
        self.assertFalse(form.is_valid())
        self.assertIn('date_completed', form.errors)
        self.assertEqual(
            form.errors['date_completed'],
            ["Date completed is required when the chore is marked as completed."]
        )

        # Test that date_completed cannot be before date_assigned
        form = ChoreAssignmentForm(data={
            'child': self.child.id,
            'chore': self.chore.id,
            'date_assigned': timezone.now().date(),
            'completed': True,
            'date_completed': timezone.now().date() - timezone.timedelta(days=1),
        })
        self.assertFalse(form.is_valid())
        self.assertIn('date_completed', form.errors)
        self.assertEqual(
            form.errors['date_completed'],
            ["Date completed cannot be earlier than the date assigned."]
        )


class ChoreTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password='testpass123')
        self.chore = ChoreFactory()

    def test_chore_list_view(self):
        """Test that the chore list view displays all chores."""
        response = self.client.get(reverse('chore_list'))
        self.assertEqual(response.status_code, 200, "Should return 200 OK.")
        self.assertContains(response, self.chore.name, msg_prefix="Chore should be in the response")
        self.assertTemplateUsed(response, 'chore_tracker/chore_list.html')

    def test_chore_create_view(self):
        """Test creating a new chore."""
        chore_count = Chore.objects.count()
        response = self.client.post(reverse('chore_create'), {
            'name': 'New Chore',
            'description': 'New Description',
            'points': 3,
        })
        self.assertEqual(response.status_code, 302, "Should redirect after successful creation")
        self.assertEqual(Chore.objects.count(), chore_count + 1, "Should create a new chore")

    def test_chore_update_view(self):
        """Test updating an existing chore."""
        response = self.client.post(reverse('chore_edit', args=[self.chore.id]), {
            'name': 'Updated Chore',
            'description': 'Updated Description',
            'points': 7,
        })
        self.assertEqual(response.status_code, 302, "Should redirect after successful update")
        self.chore.refresh_from_db()
        self.assertEqual(self.chore.name, 'Updated Chore', "Chore name should be updated")
        self.assertEqual(self.chore.points, 7, "Chore points should be updated")

    def test_chore_delete_view(self):
        """Test deleting a chore."""
        chore_count = Chore.objects.count()
        response = self.client.post(reverse('chore_delete', args=[self.chore.id]))
        self.assertEqual(response.status_code, 302, "Should redirect after successful deletion")
        self.assertEqual(Chore.objects.count(), chore_count - 1, "Should delete the chore")


class ChildTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password='testpass123')
        self.child = ChildFactory()

    def test_child_list_view(self):
        """Test that the child list view displays all children."""
        response = self.client.get(reverse('child_list'))
        self.assertEqual(response.status_code, 200, "Should return 200 OK.")
        self.assertContains(response, self.child.name, msg_prefix="Child should be in the response")
        self.assertTemplateUsed(response, 'chore_tracker/child_list.html')

    def test_child_create_view(self):
        """Test creating a new child."""
        child_count = Child.objects.count()
        response = self.client.post(reverse('child_create'), {
            'name': 'New Child',
            'age': 8,
        })
        self.assertEqual(response.status_code, 302, "Should redirect after successful creation")
        self.assertEqual(Child.objects.count(), child_count + 1, "Should create a new child")

    def test_child_update_view(self):
        """Test updating an existing child."""
        response = self.client.post(reverse('child_edit', args=[self.child.id]), {
            'name': 'Updated Child',
            'age': 11,
        })
        self.assertEqual(response.status_code, 302, "Should redirect after successful update")
        self.child.refresh_from_db()
        self.assertEqual(self.child.name, 'Updated Child', "Child name should be updated")
        self.assertEqual(self.child.age, 11, "Child age should be updated")

    def test_child_delete_view(self):
        """Test deleting a child."""
        child_count = Child.objects.count()
        response = self.client.post(reverse('child_delete', args=[self.child.id]))
        self.assertEqual(response.status_code, 302, "Should redirect after successful deletion")
        self.assertEqual(Child.objects.count(), child_count - 1, "Should delete the child")

    def test_child_age_validation(self):
        """Test that child age is validated correctly."""
        with self.assertRaises(ValidationError):
            Child.objects.create(name="Invalid Child", age=-1)

        with self.assertRaises(ValidationError):
            Child.objects.create(name="Invalid Child", age=101)


class CalendarViewTests(TestCase):
    def setUp(self):
        self.child = Child.objects.create(name="Test Child", age=10)
        self.chore = Chore.objects.create(name="Test Chore", points=5)
        self.today = timezone.now().date()

    def test_calendar_view_current_month(self):
        url = reverse('child_calendar', args=[self.child.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chore_tracker/calendar.html')
        self.assertContains(response, self.child.name)
        self.assertContains(response, self.today.strftime("%B %Y"))

    def test_calendar_view_specific_month(self):
        specific_date = self.today - timedelta(days=40)  # A date in the previous month
        url = reverse('child_calendar_date', args=[self.child.id, specific_date.year, specific_date.month])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, specific_date.strftime("%B %Y"))

    # def test_calendar_view_with_assignments(self):
    #     # Create some chore assignments
    #     ChoreAssignment.objects.create(
    #         child=self.child,
    #         chore=self.chore,
    #         date_assigned=self.today,
    #         completed=True,
    #         date_completed=self.today
    #     )
    #     ChoreAssignment.objects.create(
    #         child=self.child,
    #         chore=self.chore,
    #         date_assigned=self.today - timedelta(days=1),
    #         completed=False
    #     )
    #
    #     url = reverse('child_calendar', args=[self.child.id])
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, "Test Chore")
    #     self.assertContains(response, "Completed")
    #     self.assertContains(response, "Pending")
    #
    # def test_calendar_view_invalid_date(self):
    #     url = reverse('child_calendar_date', args=[self.child.id, 2023, 13])  # Invalid month
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, 404)


class GraphViewTests(TestCase):
    def setUp(self):
        self.child = Child.objects.create(name="Test Child", age=10)
        self.chore = Chore.objects.create(name="Test Chore", points=5)
        self.today = timezone.now().date()

        # Create some chore assignments
        for i in range(30):
            ChoreAssignment.objects.create(
                child=self.child,
                chore=self.chore,
                date_assigned=self.today - timedelta(days=i),
                completed=True,
                date_completed=self.today - timedelta(days=i)
            )

    def test_graph_view_response(self):
        url = reverse('chore_graph', args=[self.child.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chore_tracker/chore_graph.html')

    def test_graph_view_context(self):
        url = reverse('chore_graph', args=[self.child.id])
        response = self.client.get(url)
        self.assertIn('child', response.context)

    def test_graph_data_view(self):
        url = reverse('chore_graph_data', args=[self.child.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        data = json.loads(response.content)
        self.assertIn('labels', data)
        self.assertIn('datasets', data)
        self.assertEqual(len(data['labels']), 30)  # We created 30 days of data
        self.assertEqual(len(data['datasets'][0]['data']), 30)

    def test_graph_data_with_date_range(self):
        start_date = (self.today - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = self.today.strftime('%Y-%m-%d')
        url = reverse('chore_graph_data', args=[self.child.id]) + f'?start_date={start_date}&end_date={end_date}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(len(data['labels']), 8)  # 7 days + today
        self.assertEqual(len(data['datasets'][0]['data']), 8)
