from django.urls import path
from . import views

app_name = 'mailing'

urlpatterns = [
    path('', views.MailingListView.as_view(), name='list'),
    path('<int:pk>/', views.MailingDetailView.as_view(), name='detail'),
    path('create/', views.MailingCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.MailingUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.MailingDeleteView.as_view(), name='delete'),
]