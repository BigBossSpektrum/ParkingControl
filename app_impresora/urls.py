from django.urls import path
from . import views

urlpatterns = [
    path('', views.printer_dashboard, name='printer_dashboard'),
    path('add/', views.add_printer, name='add_printer'),
    path('quick-setup/', views.quick_setup_printer, name='quick_setup_printer'),
    path('windows-printers/', views.get_windows_printers, name='get_windows_printers'),
    path('test/', views.test_printer, name='test_printer'),
    path('test/<int:printer_id>/', views.test_specific_printer, name='test_specific_printer'),
    path('config/', views.printer_config, name='printer_config'),
    path('status/', views.printer_status, name='printer_status'),
    path('jobs/', views.print_jobs_list, name='print_jobs_list'),
    path('jobs/retry/<int:job_id>/', views.retry_print_job, name='retry_print_job'),
    path('print/<int:client_id>/', views.print_client_qr, name='print_client_qr'),
    path('delete/', views.delete_printer, name='delete_printer'),
    path('toggle/', views.toggle_printer_status, name='toggle_printer_status'),
    path('simulation/', views.toggle_simulation, name='toggle_simulation'),
    path('api/auto-print/', views.auto_print_qr, name='auto_print_qr'),
    path('design/save/', views.save_design_config, name='save_design_config'),
    path('design/get/', views.get_design_config, name='get_design_config'),
    path('preview/print/', views.print_preview, name='print_preview'),
]
