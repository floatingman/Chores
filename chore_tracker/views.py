import calendar
import logging
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connection
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .forms import ChoreForm, ChoreAssignmentForm
from .models import Child, Chore, ChoreAssignment

logger = logging.getLogger(__name__)


class ChoreGraphView(View):
    def get(self, request, child_id):
        child = get_object_or_404(Child, pk=child_id)
        return render(request, 'chore_tracker/chore_graph.html', {'child': child})


class ChoreGraphDataView(View):
    def get(self, request, child_id):
        try:
            child = get_object_or_404(Child, pk=child_id)

            # Get the date range from query parameters, default to last 30 days
            end_date = request.GET.get('end_date')
            start_date = request.GET.get('start_date')

            if not end_date:
                end_date = timezone.now().date()
            else:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            if not start_date:
                start_date = end_date - timedelta(days=30)
            else:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

            print(f"Date range: {start_date} to {end_date}")

            # Convert dates to strings for SQLite compatibility
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')

            # Query the database for completed chores
            if connection.vendor == 'sqlite':
                chore_data = ChoreAssignment.objects.filter(
                    child=child,
                    completed=True,
                    date_completed__gte=start_date_str,
                    date_completed__lte=end_date_str
                ).extra(
                    select={'date': "date(date_completed)"}
                ).values('date').annotate(
                    count=Count('id')
                ).order_by('date')
            else:
                chore_data = ChoreAssignment.objects.filter(
                    child=child,
                    completed=True,
                    date_completed__range=[start_date, end_date]
                ).annotate(
                    date=TruncDate('date_completed')
                ).values('date').annotate(
                    count=Count('id')
                ).order_by('date')

            print(f"Raw SQL query: {chore_data.query}")
            results = list(chore_data)
            print(f"Query results: {results}")

            # Prepare data for the graph
            dates = [item['date'] for item in results]
            counts = [item['count'] for item in results]

            response_data = {
                'labels': dates,
                'datasets': [{
                    'label': 'Chores Completed',
                    'data': counts,
                    'fill': False,
                    'borderColor': 'rgb(75, 192, 192)',
                    'tension': 0.1
                }]
            }

            print(f"Response data prepared: {response_data}")
            return JsonResponse(response_data)

        except Exception as e:
            print(f"Error in ChoreGraphDataView: {str(e)}")
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


class ChildListView(ListView):
    model = Child
    template_name = 'chore_tracker/child_list.html'
    context_object_name = 'children'


class ChildCreateView(CreateView):
    model = Child
    fields = ['name', 'age']
    template_name = 'chore_tracker/child_form.html'
    success_url = reverse_lazy('child_list')


class ChildUpdateView(UpdateView):
    model = Child
    fields = ['name', 'age']
    template_name = 'chore_tracker/child_form.html'
    success_url = reverse_lazy('child_list')


class ChildDeleteView(DeleteView):
    model = Child
    template_name = 'chore_tracker/child_confirm_delete.html'
    success_url = reverse_lazy('child_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Child was successfully deleted.")
        return super().delete(request, *args, **kwargs)


class ChoreListView(ListView):
    model = Chore
    template_name = 'chore_tracker/chore_list.html'
    context_object_name = 'chores'


class ChoreCreateView(CreateView):
    model = Chore
    fields = ['name', 'description', 'points']
    template_name = 'chore_tracker/chore_form.html'
    success_url = reverse_lazy('chore_list')


class ChoreUpdateView(UpdateView):
    model = Chore
    form_class = ChoreForm
    template_name = 'chore_tracker/chore_form.html'
    success_url = reverse_lazy('chore_list')


class ChoreDeleteView(DeleteView):
    model = Chore
    template_name = 'chore_tracker/chore_confirm_delete.html'
    success_url = reverse_lazy('chore_list')


class ChoreAssignmentListView(ListView):
    model = ChoreAssignment
    template_name = 'chore_tracker/chore_assignment_list.html'
    context_object_name = 'chore_assignments'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('child', 'chore')
        ordering = self.request.GET.get('order_by', '-date_assigned')
        if ordering not in ['date_assigned', '-date_assigned', 'child_name', 'chore_name', 'completed']:
            ordering = '-date_assigned'
        if ordering == 'child_name':
            return queryset.order_by('child__name', '-date_assigned')
        elif ordering == 'chore_name':
            return queryset.order_by('chore__name', '-date_assigned')
        return queryset.order_by(ordering, '-date_assigned')


class ChoreAssignmentCreateView(CreateView):
    model = ChoreAssignment
    form_class = ChoreAssignmentForm
    template_name = 'chore_tracker/chore_assignment_form.html'
    success_url = reverse_lazy('chore_assignment_list')

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class ChoreAssignmentUpdateView(UpdateView):
    model = ChoreAssignment
    form_class = ChoreAssignmentForm
    template_name = 'chore_tracker/chore_assignment_form.html'
    success_url = reverse_lazy('chore_assignment_list')


class ChoreAssignmentDeleteView(DeleteView):
    model = ChoreAssignment
    template_name = 'chore_tracker/chore_assignment_confirm_delete.html'
    success_url = reverse_lazy('chore_assignment_list')


class ChoreAssignmentCompleteView(UpdateView):
    model = ChoreAssignment
    fields = ['completed', 'date_completed']

    def form_valid(self, form):
        form.instance.completed = True
        form.instance.date_completed = form.cleaned_data.get('date_completed') or timezone.now().date()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('chore_assignment_list')


class ChildPointsView(View):
    def get(self, request, child_id):
        child = get_object_or_404(Child, pk=child_id)
        context = {
            'child': child,
            'daily_points': child.get_points(period='day'),
            'weekly_points': child.get_points(period='week'),
            'monthly_points': child.get_points(period='month'),
            'total_points': child.get_points(period='all'),
        }
        return render(request, 'chore_tracker/child_points.html', context)


class CalendarView(View):
    def get(self, request, child_id, year=None, month=None):
        child = get_object_or_404(Child, pk=child_id)

        if year is None:
            year = timezone.now().year
        if month is None:
            month = timezone.now().month

        # Create a calendar object
        cal = calendar.monthcalendar(year, month)

        # Get all completed chore assignments for the month
        start_date = datetime(year, month, 1)
        end_date = start_date + timedelta(days=calendar.monthrange(year, month)[1])
        assignments = ChoreAssignment.objects.filter(
            child=child,
            completed=True,
            date_completed__range=[start_date, end_date]
        )

        # Create a dictionary of daily points
        daily_points = {}
        for assignment in assignments:
            date = assignment.date_completed
            if date in daily_points:
                daily_points[date] += assignment.chore.points
            else:
                daily_points[date] = assignment.chore.points

        # Create calendar data
        calendar_data = []
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append({'day': '', 'points': ''})
                else:
                    date = datetime(year, month, day).date()
                    points = daily_points.get(date, 0)
                    week_data.append({'day': day, 'points': points})
            calendar_data.append(week_data)

        # Get previous and next month links
        prev_month = datetime(year, month, 1) - timedelta(days=1)
        next_month = datetime(year, month, 1) + timedelta(days=31)

        context = {
            'child': child,
            'calendar_data': calendar_data,
            'month': datetime(year, month, 1),
            'prev_month': prev_month,
            'next_month': next_month,
        }
        return render(request, 'chore_tracker/calendar.html', context)









class ChoreAssignmentUpdateView(UpdateView):
    model = ChoreAssignment
    form_class = ChoreAssignmentForm
    template_name = 'chore_tracker/chore_assignment_form.html'
    success_url = reverse_lazy('chore_assignment_list')


class ChoreAssignmentDeleteView(LoginRequiredMixin, DeleteView):
    model = ChoreAssignment
    template_name = 'chore_tracker/chore_assignment_confirm_delete.html'
    success_url = reverse_lazy('chore_assignment_list')
