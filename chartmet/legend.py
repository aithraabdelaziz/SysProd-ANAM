from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from .models import Legend
from django.contrib.auth.decorators import permission_required, login_required, permission_required
from pprint import pprint
CLASS_NUMBER = 101

@permission_required(['chartmet.add_legend', 'chartmet.change_legend', 'chartmet.delete_legend'], raise_exception=True)
def manage_legends(request):
    legends = Legend.objects.all()
    return render(request, 'legends/manage_legends.html', {'legends': legends})
@permission_required('chartmet.add_legend', raise_exception=True)
def add_legend(request):
    if request.method == 'POST':
        form = LegendForm(request.POST)
        if form.is_valid():
            desc = to_description(request.POST)
            form.instance.descriptions = desc
            form.save()
            return redirect('chartmet:manage_legends')
    else:
        form = LegendForm()
    ### default classes 
    desc = default_legend()
    return render(request, 'legends/add_legend.html',{'form': form, 'descriptions':desc})
@permission_required('chartmet.change_legend', raise_exception=True)
def activate_legend(request, legend_id):
    legend = get_object_or_404(Legend, id=legend_id)
    legend.active = True
    legend.save()
    return redirect('chartmet:manage_legends')
@permission_required('chartmet.change_legend', raise_exception=True)
def deactivate_legend(request, legend_id):
    legend = get_object_or_404(Legend, id=legend_id)
    legend.active = False
    legend.save()
    return redirect('chartmet:manage_legends')
@permission_required('chartmet.delete_legend', raise_exception=True)
def delete_legend(request, legend_id):
    legend = get_object_or_404(Legend, id=legend_id)
    legend.delete()
    return redirect('chartmet:manage_legends') 
@permission_required('chartmet.change_legend', raise_exception=True)
def edit_legend(request, legend_id):
    legend = get_object_or_404(Legend, id=legend_id)
    if request.method == 'POST':
        form = LegendForm(request.POST, instance=legend)
        if form.is_valid():
            desc = to_description(request.POST)
            form.instance.descriptions = desc
            pprint(form)
            legend = form.save()
            pprint(legend)
            return redirect('chartmet:manage_legends')
    else:
        form = LegendForm(instance=legend)

    ### default classes 
    desc = default_legend(legend.descriptions)
    return render(request, 'legends/add_legend.html', {'legend': legend, 'form': form,'descriptions':desc})
######################
def to_description(tab):
	description ={}
	for i in range(CLASS_NUMBER):
		key = f'classe_{i}'
		if key in tab :
			if len(tab[key]) > 0 and len(tab['desc_'+str(i)]) > 0  and len(tab['color_'+str(i)]) > 0 :
				description[tab[key]] = {
										"description": tab['desc_'+str(i)], 
										"color": tab['color_'+str(i)]
										}
	return description
def default_legend(desc=None):
	if desc == None : desc = {"0" : {"description":"c0","color":"#00FF00"},"1" : {"description":"c1","color":"#FF0000"}}
	l = {}
	i = 0
	for k,v in desc.items():
		l[str(i)]={k:v}
		i += 1
	while i < CLASS_NUMBER-1 :
		
		l[str(i)]={str(i):{"description":"","color":""}}
		i += 1
		
	return l