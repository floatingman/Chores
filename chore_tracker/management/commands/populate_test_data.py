import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from chore_tracker.models import Child, Chore, ChoreAssignment


class Command(BaseCommand):
    help = 'Populates the database with test data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating database...')

        # Create children
        children = [
            Child.objects.create(name="Alice", age=8),
            Child.objects.create(name="Bob", age=10),
            Child.objects.create(name="Charlie", age=12)
        ]

        # Create chores
        chores = [
            Chore.objects.create(name="Make bed", description="Straighten sheets and comforter", points=1),
            Chore.objects.create(name="Do dishes", description="Load and run dishwasher", points=2),
            Chore.objects.create(name="Take out trash", description="Empty all trash bins and take to curb", points=2),
            Chore.objects.create(name="Vacuum living room", description="Vacuum carpets and rugs", points=3),
            Chore.objects.create(name="Mow lawn", description="Mow front and back yard", points=5)
        ]

        # Create chore assignments
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        for _ in range(100):  # Create 100 random assignments
            child = random.choice(children)
            chore = random.choice(chores)
            date_assigned = start_date + timedelta(days=random.randint(0, 30))
            completed = random.choice([True, False])
            date_completed = date_assigned + timedelta(days=random.randint(0, 3)) if completed else None

            ChoreAssignment.objects.create(
                child=child,
                chore=chore,
                date_assigned=date_assigned,
                completed=completed,
                date_completed=date_completed
            )

        self.stdout.write(self.style.SUCCESS('Successfully populated database with test data'))
