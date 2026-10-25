from django.urls import path
from . import views

urlpatterns = [
    path('', views.perfilU, name='perfilU'),
    path('graficos/', views.graficosU, name='graficosU'),

]