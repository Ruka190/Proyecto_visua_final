from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicioU, name='inicioU'),
    path('perfilU/', views.perfilU, name='perfilU'),
    path('graficos/', views.graficosU, name='graficosU'),


]