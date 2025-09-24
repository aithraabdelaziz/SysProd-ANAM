from django.shortcuts import render

def home(request):
    return render(request, 'home/dashboard.html')
def maintenance(request):
    return render(request, 'maintenance_page.html')
