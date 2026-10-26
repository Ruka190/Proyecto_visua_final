from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicioU, name='inicioU'),
    path('perfilU/', views.perfilU, name='perfilU'),
    path('graficos/', views.graficosU, name='graficosU'),
    path('administrador/', views.administrador, name= 'administrador'),
    path('administrador/inicio/', views.admin_inicio, name='admin_inicio'),
    path('administrador/estadisticas/', views.admin_estadisticas, name='admin_estadisticas'),
    path('administrador/notificaciones/', views.admin_notificaciones, name='admin_notificaciones'),


]