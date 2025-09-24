from . import views 
from django.urls import path
app_name = 'home'
urlpatterns = [
    path('', views.home, name='home'),
    path('home', views.home, name='home'),
    path('maintenance', views.maintenance, name='maintenance'),
]
