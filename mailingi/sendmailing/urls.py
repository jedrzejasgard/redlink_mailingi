from django.urls import path

from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('reg/', views.wyslijmailingReg, name='wyslijmailingReg'),
    path('vip/', views.wyslijmailingVip, name='wyslijmailingVIP'),
    path('wyslij_test/', views.wyslij_test, name='wyslij_test'),
    path('wyslij_mailing/', views.wyslij_mailing, name='wyslij_mailing'),
    path('wyslij_mailing_vip/', views.wyslij_mailing_vip, name='wyslij_mailing_vip'),
    path('zestawienie_kampanii/', views.zestawienie_kampanii, name='zestawienie_kampanii'),
    path('detale_kampanii/', views.detale_kampanii, name='detale_kampanii'),
    path('blad_nazwy/', views.blad_nazwy, name='blad_nazwy'),
    path('generuj_stats/', views.generuj_stats, name='generuj_stats')

]