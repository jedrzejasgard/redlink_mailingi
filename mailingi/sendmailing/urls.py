from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='wyslijmailing'),
    path('wyslij_test/', views.wyslij_test, name='wyslij_test'),
    path('wyslij_mailing/', views.wyslij_mailing, name='wyslij_mailing'),
    path('zestawienie_kampanii/', views.zestawienie_kampanii, name='zestawienie_kampanii'),
    path('detale_kampanii/', views.detale_kampanii, name='detale_kampanii'),
    path('blad_nazwy/', views.blad_nazwy, name='blad_nazwy')
]