
from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.http import HttpResponseRedirect
# Create your views here.
def index(request):
    return render(request,'wyslijmailing.html')