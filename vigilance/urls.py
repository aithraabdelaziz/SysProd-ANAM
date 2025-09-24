from django.urls import path
from . import views
app_name = 'vigilance'
urlpatterns = [
    path('', views.vigilance_map, name='vigilance_map'),           # page carte
    path('edit_vigilance/', views.edit_vigilance, name='edit_vigilance'),  # API save
    path('add_vigilance/', views.add_vigilance, name='add_vigilance'),
    path('get_vigilance/', views.get_vigilance, name='get_vigilance'),
    path('clear_vigilance/', views.clear_vigilance, name='clear_vigilance'),
    path('revoke_vigilance/', views.revoke_vigilance, name='revoke_vigilance'),
    path('generate_cap_messages/', views.generate_cap_messages, name='generate_cap_messages'),
    path('save_cap/', views.save_cap, name='save_cap'),
    path('show_image/', views.show_image, name='show_image'),
    path('export/', views.export, name='export'),
]

