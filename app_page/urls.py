from django.urls import path

from . import views

urlpatterns = [
    path('logout/', views.logout_view, name='logout'),
    path('salida/', views.salida_qr, name='salida_qr'),
    path('portal/', views.portal_opciones, name='portal_opciones'),
    path('index/', views.dashboard, name='index'),  # Redirigir index al dashboard
    path('', views.dashboard, name='dashboard'),
    
    # URLs para parking
    path('parking/', views.dashboard_parking, name='dashboard_parking'),
    
    # URLs para visitantes
    path('visitantes/', views.dashboard_visitante, name='dashboard_visitante'),
    path('visitantes/lista/', views.lista_visitantes, name='lista_visitantes'),
    path('visitantes/editar/<int:pk>/', views.editar_visitante, name='editar_visitante'),
    path('visitantes/eliminar/<int:pk>/', views.eliminar_visitante, name='eliminar_visitante'),
    path('visitantes/ver/<int:pk>/', views.ver_visitante, name='ver_visitante'),
    
    # URLs para clientes (parking)
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/editar/<int:pk>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/eliminar/<int:pk>/', views.eliminar_cliente, name='eliminar_cliente'),
    path('clientes/registro/<int:pk>/', views.ver_registro, name='ver_registro'),
    
    # URLs para configuración
    path('configurar-costos/', views.configurar_costos, name='configurar_costos'),
    path('toggle-tarifa-plena/', views.toggle_tarifa_plena, name='toggle_tarifa_plena'),
    
    # URLs para recaudación
    path('resumen-recaudacion/', views.resumen_recaudacion, name='resumen_recaudacion'),
    path('corte-recaudacion/', views.realizar_corte_recaudacion, name='corte_recaudacion'),
]

