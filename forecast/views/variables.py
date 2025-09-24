from django.shortcuts import render, redirect, get_object_or_404
from forecast.forms import *
from forecast.models import Variable
from django.contrib.auth.decorators import permission_required, login_required, permission_required


CLASS_NUMBER = 101
from django.template.defaulttags import register
# from django.contrib.auth.models import Group
@register.simple_tag
def increment(value, incr=1):
    return value + incr
# @register.filter(name='in_group')
# def in_group(user, group_name):
#     try:
#         group = Group.objects.get(name=group_name)
#         return group in user.groups.all()
#     except Group.DoesNotExist:
#         return False


################ Views for Varibales ###################################

@permission_required(['forecast.add_variable', 'forecast.change_variable', 'forecast.delete_variable'], raise_exception=True)
def manage_variables(request):
    variables = Variable.objects.all()
    return render(request, 'variables/manage_variables.html', {'variables': variables})
@permission_required('forecast.add_variable', raise_exception=True)
def add_variable(request):
    if request.method == 'POST':
        form = VariableForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('forecast:manage_variables')
    else:
        form = VariableForm()    

    return render(request, 'variables/add_variable.html',{'form': form})
@permission_required('forecast.change_variable', raise_exception=True)
def activate_variable(request, variable_id):
    variable = get_object_or_404(Variable, id=variable_id)
    variable.active = True
    variable.save()
    return redirect('forecast:manage_variables')
@permission_required('forecast.change_variable', raise_exception=True)
def deactivate_variable(request, variable_id):
    variable = get_object_or_404(Variable, id=variable_id)
    variable.active = False
    variable.save()
    return redirect('forecast:manage_variables')
@permission_required('forecast.delete_variable', raise_exception=True)
def delete_variable(request, variable_id):
    variable = get_object_or_404(Variable, id=variable_id)
    variable.delete()
    return redirect('forecast:manage_variables') 
@permission_required('forecast.change_variable', raise_exception=True)
def edit_variable(request, variable_id):
    variable = get_object_or_404(Variable, id=variable_id)
    if request.method == 'POST':
        form = VariableForm(request.POST, instance=variable)
        if form.is_valid():
            variable = form.save()
            return redirect('forecast:manage_variables')
    else:
        form = VariableForm(instance=variable)

    return render(request, 'variables/add_variable.html', {'variable': variable, 'form': form})
