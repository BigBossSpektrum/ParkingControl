from django.urls import path
from . import views

urlpatterns = [
    path('', views.printer_dashboard, name='printer_dashboard'),
    path('test/', views.test_printer, name='test_printer'),
    path('config/', views.printer_config, name='printer_config'),
    path('status/', views.printer_status, name='printer_status'),
    path('jobs/', views.print_jobs_list, name='print_jobs_list'),
    path('print/<int:client_id>/', views.print_client_qr, name='print_client_qr'),
    path('delete/<int:printer_id>/', views.delete_printer, name='delete_printer'),
    path('toggle/<int:printer_id>/', views.toggle_printer_status, name='toggle_printer_status'),
    path('simulation/', views.toggle_simulation_mode, name='toggle_simulation_mode'),
    path('api/auto-print/', views.auto_print_qr, name='auto_print_qr'),
]
