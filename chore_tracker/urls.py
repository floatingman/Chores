from django.urls import path
from . import views

urlpatterns = [
  path('children/', views.ChildListView.as_view(), name='child_list'),
  path('children/create/', views.ChildCreateView.as_view(), name='child_create'),
  path('children/<int:child_id>/points/', views.ChildPointsView.as_view(), name='child_points'),
  path('children/<int:child_id>/calendar/', views.CalendarView.as_view(), name='child_calendar'),
  path('children/<int:child_id>/calendar/<int:year>/<int:month>/', views.CalendarView.as_view(), name='child_calendar_date'),
  path('children/<int:child_id>/graph/', views.ChoreGraphView.as_view(), name='chore_graph'),
  path('children/<int:child_id>/graph/data/', views.ChoreGraphDataView.as_view(), name='chore_graph_data'),
  path('child/add/', views.ChildCreateView.as_view(), name='child_create'),
  path('child/<int:pk>/edit/', views.ChildUpdateView.as_view(), name='child_edit'),
  path('children/<int:pk>/delete/', views.ChildDeleteView.as_view(), name='child_delete'),

  path('assignments/', views.ChoreAssignmentListView.as_view(), name='chore_assignment_list'),
  path('assignments/create/', views.ChoreAssignmentCreateView.as_view(), name='chore_assignment_create'),
  path('assignments/<int:pk>/edit/', views.ChoreAssignmentUpdateView.as_view(), name='chore_assignment_edit'),
  path('assignments/<int:pk>/delete/', views.ChoreAssignmentDeleteView.as_view(), name='chore_assignment_delete'),
  path('assignments/<int:pk>/complete/', views.ChoreAssignmentCompleteView.as_view(), name='chore_assignment_complete'),

  path('chores/', views.ChoreListView.as_view(), name='chore_list'),
  path('chores/create/', views.ChoreCreateView.as_view(), name='chore_create'),
  path('chores/<int:pk>/delete/', views.ChoreDeleteView.as_view(), name='chore_delete'),
  path('chores/<int:pk>/edit/', views.ChoreUpdateView.as_view(), name='chore_edit'),
]