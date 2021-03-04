
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from .models import KampaniaRedlink
import configparser
import configparser
import requests
import zeep
import datetime
import json
import re
# Create your views here.

config = configparser.ConfigParser()
configFilePath = 'C:/Users/asgard_48/Documents/Skrypty/BAZA TESTOWA - WGRYWANIE WD/baza mail/redlink.ini'
config.read(configFilePath)

usr = config.get('redlink', 'redlink_API_user')
passw = config.get('redlink', 'redlink_API_pass')


def index(request):
    return render(request, 'wyslijmailing.html')


def blad_nazwy(request):
    return render(request, 'blad_nazwy.html')


def zestawienie_kampanii(request):
    kampanie_model = KampaniaRedlink.objects.all().values()
    return render(request, 'zestawienie_kampanii.html', {'kampanie': kampanie_model})


def wyslij_test_redlink(nazwa_mailingu, temat, imie_nazwisko, mail_wysylki, content_mailingu):
    mail = zeep.Client("https://redlink.pl/ws/v1/Soap/MailCampaigns/MailCampaigns.asmx?WSDL")
    data = {'Name': nazwa_mailingu, 'Subject': '   TEST   ' + temat, 'FromName': imie_nazwisko,
            'FromAddress': mail_wysylki, 'HtmlFromWebSiteUrl': content_mailingu,
            'GroupId': '66F3AE43-6DDC-475E-8DB6-6775EBF9030D', 'TrackLinks': True}
    # print(data)
    response = mail.service.CreateMailCampaign(strUserName=usr, strPassword=passw, data=data)
    r_json = zeep.helpers.serialize_object(response)
    # print(r_json)
    print(r_json['Data'])


def wyslij_test(request):
    if request.method == "POST":
        dane_mailing_post = request.POST['formMailingTest']
        dane_mailing = json.loads(dane_mailing_post)
        dane_na_strone = {'nazwa_mailingu': dane_mailing['nazwa_mailingu'],
                          'temat_PL': dane_mailing['temat_PL'].replace(' ', '_'),
                          'temat_DE': dane_mailing['temat_DE'].replace(' ', '_'),
                          'temat_EN': dane_mailing['temat_EN'].replace(' ', '_'),
                          'temat_FR': dane_mailing['temat_FR'].replace(' ', '_'),
                          'adres_strony_mailingu': dane_mailing['adres_strony_mailingu']}
        wyslij_test_redlink(dane_mailing['nazwa_mailingu'], dane_mailing['temat_PL'], 'Marketing ASGARD',
                            'marketing@asgard.gifts', dane_mailing['adres_strony_mailingu'])
        return render(request, 'wyslijmailing.html', {'dane': dane_na_strone })


def wyslij_test_redlink(nazwa_mailingu, temat, imie_nazwisko, mail_wysylki, content_mailingu):
    mail = zeep.Client("https://redlink.pl/ws/v1/Soap/MailCampaigns/MailCampaigns.asmx?WSDL")
    data = {'Name': nazwa_mailingu, 'Subject': '   TEST   ' + temat, 'FromName': imie_nazwisko,
            'FromAddress': mail_wysylki, 'HtmlFromWebSiteUrl': content_mailingu,
            'GroupId': '66F3AE43-6DDC-475E-8DB6-6775EBF9030D', 'TrackLinks': True}
    # print(data)
    response = mail.service.CreateMailCampaign(strUserName=usr, strPassword=passw, data=data)
    r_json = zeep.helpers.serialize_object(response)
    # print(r_json)
    print(r_json['Data'])
