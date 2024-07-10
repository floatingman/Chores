import calendar
from datetime import datetime, timedelta

from django.contrib import messages
from django.db import connection
from django.db.models import Count, F
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView
from django.views.generic.edit import UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import ChildForm, ChoreForm, ChoreAssignmentForm
from .models import Child, Chore, ChoreAssignment
import logging

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


class ChildListView(View):
    def get(self, request):
        children = Child.objects.all()
        return render(request, 'chore_tracker/child_list.html',
                      {'children': children})


class ChildCreateView(View):
    def get(self, request):
        form = ChildForm()
        return render(request, 'chore_tracker/child_form.html', {'form': form})

    def post(self, request):
        form = ChildForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('child_list')
        return render(request, 'chore_tracker/child_form.html', {'form': form})


class ChildUpdateView(UpdateView):
    model = Child
    form_class = ChildForm
    template_name = 'chore_tracker/child_form.html'
    success_url = reverse_lazy('child_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Child'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        # You can add a success message here if you want
        # messages.success(self.request, 'Child updated successfully.')
        return response


class ChoreListView(View):
    def get(self, request):
        chores = Chore.objects.all()
        return render(request, 'chore_tracker/chore_list.html', {'chores': chores})


class ChoreCreateView(View):
    def get(self, request):
        form = ChoreForm()
        return render(request, 'chore_tracker/chore_form.html', {'form': form})

    def post(self, request):
        form = ChoreForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('chore_list')
        return render(request, 'chore_tracker/chore_form.html', {'form': form})


class ChoreAssignmentCreateView(View):
    def get(self, request):
        form = ChoreAssignmentForm()
        return render(request, 'chore_tracker/chore_assignment_form.html',
                      {'form': form})

    def post(self, request):
        form = ChoreAssignmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('chore_assignment_list')
        return render(request, 'chore_tracker/chore_assignment_form.html',
                      {'form': form})


class ChoreAssignmentListView(ListView):
    model = ChoreAssignment
    template_name = 'chore_tracker/chore_assignment_list.html'
    context_object_name = 'chore_assignments'
    paginate_by = 10

    def get_queryset(self):
        queryset = ChoreAssignment.objects.select_related('child', 'chore')

        # Get the ordering from the URL parameters
        ordering = self.request.GET.get('order_by', '-date_assigned')

        # Define allowed fields and their database representations
        allowed_fields = {
            'date_assigned': F('date_assigned'),
            'child_name': F('child__name'),
            'chore_name': F('chore__name'),
            'completed': F('completed')
        }

        # Check if the ordering is allowed and add direction
        order_field = ordering.lstrip('-')
        if order_field in allowed_fields:
            order_expression = allowed_fields[order_field]
            if ordering.startswith('-'):
                order_expression = order_expression.desc()
            queryset = queryset.order_by(order_expression, '-id')
        else:
            # Default ordering if not specified or invalid
            queryset = queryset.order_by('-date_assigned', '-id')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_ordering'] = self.request.GET.get('order_by', '-date_assigned')
        return context


class ChoreAssignmentCompleteView(View):
    def post(self, request, pk):
        assignment = get_object_or_404(ChoreAssignment, pk=pk)
        assignment.completed = True
        assignment.date_completed = timezone.now().date()
        assignment.save()
        return redirect('chore_assignment_list')


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


class ChoreUpdateView(UpdateView):
    model = Chore
    form_class = ChoreForm
    template_name = 'chore_tracker/chore_form.html'
    success_url = reverse_lazy('chore_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Chore'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request,
                         f'Chore "{self.object.name}" updated successfully.')
        return response


class ChoreAssignmentUpdateView(UpdateView):
    model = ChoreAssignment
    form_class = ChoreAssignmentForm
    template_name = 'chore_tracker/chore_assignment_form.html'
    success_url = reverse_lazy('chore_assignment_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Chore Assignment'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Chore assignment updated successfully.')
        return response


class ChoreAssignmentDeleteView(LoginRequiredMixin, DeleteView):
    model = ChoreAssignment
    template_name = 'chore_tracker/chore_assignment_confirm_delete.html'
    success_url = reverse_lazy('chore_assignment_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Chore Assignment'
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Chore assignment was successfully deleted.')
        return super().delete(request, *args, **kwargs)


class ChoreDeleteView(LoginRequiredMixin, DeleteView):
    model = Chore
    template_name = 'chore_tracker/chore_confirm_delete.html'
    success_url = reverse_lazy('chore_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Chore'
        return context

    def delete(self, request, *args, **kwargs):
        chore = self.get_object()
        messages.success(self.request, f'Chore "{chore.name}" was successfully deleted.')
        return super().delete(request, *args, **kwargs)