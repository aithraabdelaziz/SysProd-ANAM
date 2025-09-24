from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import permission_required, login_required, permission_required


CLASS_NUMBER = 101
from django.template.defaulttags import register
############# Views for Forecast####################@
##################################################@
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin
from forecast.models import Forecast
from forecast.forms import ForecastForm, ForecastFilterForm

class ForecastListView(PermissionRequiredMixin, ListView):
    model = Forecast
    template_name = 'forecast/forecast_list.html'
    context_object_name = 'forecasts'
    permission_required = 'forecast.view_forecast'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        form = ForecastFilterForm(self.request.GET)
        
        if form.is_valid():
            data = form.cleaned_data
            if data['zone']:
                queryset = queryset.filter(zone=data['zone'])
            if data['parametre']:
                queryset = queryset.filter(parametre=data['parametre'])
            if data['date_debut']:
                queryset = queryset.filter(date__gte=data['date_debut'])
            if data['date_fin']:
                queryset = queryset.filter(date__lte=data['date_fin'])
            if data['echeance'] is not None:
                queryset = queryset.filter(echeance=data['echeance'])
        
        return queryset.order_by('-date', 'zone')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ForecastFilterForm(self.request.GET)
        return context

class ForecastCreateView(PermissionRequiredMixin, CreateView):
    model = Forecast
    form_class = ForecastForm
    template_name = 'forecast/forecast_form.html'
    success_url = reverse_lazy('forecast:forecast_list')
    permission_required = 'forecast.add_forecast'

class ForecastUpdateView(PermissionRequiredMixin, UpdateView):
    model = Forecast
    form_class = ForecastForm
    template_name = 'forecast/forecast_form.html'
    success_url = reverse_lazy('forecast:forecast_list')
    permission_required = 'forecast.change_forecast'

class ForecastDeleteView(PermissionRequiredMixin, DeleteView):
    model = Forecast
    template_name = 'forecast/forecast_confirm_delete.html'
    success_url = reverse_lazy('forecast:forecast_list')
    permission_required = 'forecast.delete_forecast'


