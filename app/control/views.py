from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.
def home(request):
	"""Vista principal de la app `control` para verificar que la app responde."""
	return HttpResponse("Control app: funciona correctamente.")
