from django.urls import path
from .views import diffusion_view,bulletin_pdf_view,historique_transmissions #,send_bulletins
app_name = 'dissiminate'
urlpatterns = [
    # path('send/', send_bulletins, name='send_bulletins'),
    path('diffusion/', diffusion_view, name='diffusion'),
    # path("api/affbulletin/<int:pk>/pdf-url/", bulletin_pdf_url, name="bulletin-pdf-url"),
    path('pdf/<int:pk>/', bulletin_pdf_view, name='bulletin_pdf_view'),

    path('historique/', historique_transmissions, name='transmission_history'),



]