
from django.shortcuts import redirect, render

def home(request):
    # return redirect('admin:index')
    return render(request, 'home.html')

