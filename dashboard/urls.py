from django.urls import path
from . import views

urlpatterns = [
    ## Index
    path('', views.index, name='index'),
    path('contacto/', views.contacto, name='contacto'),
    path('faq/', views.faq, name='faq'),
    path('nuestra-mision/', views.mision, name='mision'),

    ## Usuario
    path('usuario/', views.inicioU, name='inicioU'),
    path('usuario/perfilU/', views.perfilU, name='perfilU'),
    path('usuario/graficos/', views.graficosU, name='graficosU'),
    
    ## Administrador
    path('administrador/', views.administrador, name= 'administrador'),
    path('administrador/inicio/', views.admin_inicio, name='admin_inicio'),
    path('administrador/estadisticas/', views.admin_estadisticas, name='admin_estadisticas'),
    path('administrador/notificaciones/', views.admin_notificaciones, name='admin_notificaciones'),
    path('administrador/usuarios/', views.admin_usuarios, name='admin_usuarios')


]