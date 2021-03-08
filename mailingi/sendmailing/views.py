
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from .models import KampaniaRedlink, Handlowiec
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


def szczegoly_kampanii_redlink(id_kampanii, data_wyslania):
    try:
        redlink_kampania = zeep.Client('https://redlink.pl/ws/v1/Soap/MailCampaigns/MailCampaigns.asmx?WSDL')
        client = zeep.Client('https://redlink.pl/ws/v1/Soap/Contacts/Groups.asmx?WSDL')
        response_bounce = redlink_kampania.service.GetMailCampaignBouncesReport(strUserName=usr,
                                                                                strPassword=passw,
                                                                                strCampaignId=id_kampanii,
                                                                                dateFrom=str(data_wyslania),
                                                                                dateTo=str(datetime.date.today()),
                                                                                offset=0,
                                                                                limit=10000)
        response_ctr = redlink_kampania.service.GetMailCampaignCtrReport(strUserName=usr,
                                                                         strPassword=passw,
                                                                         strCampaignId=id_kampanii,
                                                                         dateFrom=str(data_wyslania),
                                                                         dateTo=str(datetime.date.today()),
                                                                         offset=0,
                                                                         limit=10000)
        response_data = redlink_kampania.service.GetMailCampaignData(strUserName=usr,
                                                                     strPassword=passw,
                                                                     strCampaignId=id_kampanii)
        response_or = redlink_kampania.service.GetMailCampaignOrReport(strUserName=usr,
                                                                       strPassword=passw,
                                                                       strCampaignId=id_kampanii,
                                                                       dateFrom=str(data_wyslania),
                                                                       dateTo=str(datetime.date.today()),
                                                                       offset=0,
                                                                       limit=10000)
        response_unsub = redlink_kampania.service.GetMailCampaignUnregistrationsReport(strUserName=usr,
                                                                                       strPassword=passw,
                                                                                       strCampaignId=id_kampanii,
                                                                                       dateFrom=str(data_wyslania),
                                                                                       dateTo=str(datetime.date.today()),
                                                                                       offset=0,
                                                                                       limit=10000 )
        r_json_bounce = zeep.helpers.serialize_object(response_bounce)
        r_json_ctr = zeep.helpers.serialize_object(response_ctr)
        r_json_data = zeep.helpers.serialize_object(response_data)
        r_json_or = zeep.helpers.serialize_object(response_or)
        group_id = r_json_data['Data']['GroupId']
        response_group_count = client.service.GetGroupContactsCount(strUserName=usr,
                                                                    strPassword=passw,
                                                                    strGroupId=group_id)
        r_json_groupcount = zeep.helpers.serialize_object(response_group_count)
        r_json_unsub = zeep.helpers.serialize_object(response_unsub)
        try:
            un_sub = len(r_json_unsub['Results'])
        except:
            un_sub = 0
        clicks = 0
        for item in r_json_ctr['Results']['MailCampaignCtrData']:
            clicks += int(item['Count'])
        bounces = len(r_json_bounce['Results']['MailCampaignBounceData'])
        otwarte_maile = len(r_json_or['Results']['MailCampaignOrData'])
        dostarczone_wiadomosci = int(r_json_groupcount['Data']) - int(bounces)
        ctr = round(clicks*100/dostarczone_wiadomosci, 2)
        open_rate = round(otwarte_maile*100/dostarczone_wiadomosci, 2)
        dane = [ctr, open_rate, dostarczone_wiadomosci, un_sub]
    except:
        dane = ['blad', 'blad', 'blad', 'blad']
    return dane


def detale_kampanii(request):
    if request.method == "POST":
        id_kampanii = (request.POST['form_id_kampanii'])
        kampanie_model = KampaniaRedlink.objects.filter(id=str(id_kampanii)).values()
        mailing_dane = {}
        for kampania in kampanie_model:
            data_wyslania = str(kampania['kiedy_wyslany'].split(' ')[0])
            for item in kampania:
                item2 = item.split('_')
                if item2[0] == 'redlink':
                    id_redlink = kampania[item]
                    mailing_dane[id_redlink] = (szczegoly_kampanii_redlink(id_redlink, data_wyslania))
    return render(request, 'detale_kampanii.html', {'szczegoly': kampanie_model,
                                                    'dict_mailingi_szczegoly': mailing_dane})


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
        return render(request, 'wyslijmailing.html', {'dane': dane_na_strone})


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


def wyslij_mailing_redlink(nazwa_mailingu, temat, imie_nazwisko, mail_wysylki, content_mailingu, data_wyslania, grup_id):
    mail = zeep.Client("https://redlink.pl/ws/v1/Soap/MailCampaigns/MailCampaigns.asmx?WSDL")
    data = {'Name': nazwa_mailingu, 'Subject': temat, 'FromName': imie_nazwisko, 'FromAddress': mail_wysylki,
            'HtmlFromWebSiteUrl': content_mailingu, 'GroupId': grup_id, 'ScheduleTime': data_wyslania,
            'TrackLinks': True}
    # print(data_wyslania)
    response = mail.service.CreateMailCampaign(strUserName=usr, strPassword=passw, data=data)
    r_json = zeep.helpers.serialize_object(response)
    # print(r_json)
    return str(r_json['Data'])


def show_all_grups():
    client = zeep.Client('https://redlink.pl/ws/v1/Soap/Contacts/Groups.asmx?WSDL')
    response = client.service.GetAllGroups(strUserName=usr, strPassword=passw)
    r_json = zeep.helpers.serialize_object(response)
    return r_json['DataArray']['GroupData']


def wyslij_mailing(request):
    if request.method == "POST":
        lista_jezykow = ['PL', 'EN', 'DE', 'FR']
        dane_mailing_post = request.POST['formMailing']
        dane_mailing = json.loads(dane_mailing_post)
        tematy_mailingu = {}
        nazwa_mailingu = dane_mailing['nazwa_mailingu']
        try:
            print(KampaniaRedlink.objects.filter(nazwa_kampanii=nazwa_mailingu).values())
            len(KampaniaRedlink.objects.filter(nazwa_kampanii=nazwa_mailingu).values()[0])
            return redirect('http://127.0.0.1:8000/blad_nazwy')
        except:
            print('wysyłam nowy mailing')
            tematy_mailingu['PL'] = dane_mailing['temat_PL'].replace('_', ' ')
            tematy_mailingu['EN'] = dane_mailing['temat_EN'].replace('_', ' ')
            tematy_mailingu['DE'] = dane_mailing['temat_DE'].replace('_', ' ')
            tematy_mailingu['FR'] = dane_mailing['temat_FR'].replace('_', ' ')
            # print(tematy_mailingu)
            adres_strony_mailingu = dane_mailing['adres_strony_mailingu']
            data_wysylki_input = dane_mailing['data_wysylki_input'].replace(':', '-')
            year, month, day, hour, minute, second = map(int, data_wysylki_input.split('-'))
            data_wyslania = datetime.datetime(year, month, day, hour, minute, second)

            # data_wyslania_przypomnienie = datetime.datetime(year, month, day+2, hour, minute, second)
            # print(data_wyslania_przypomnienie)

            # wyslij_do_asgardian_redlink(dane_mailing['nazwa_mailingu'],tematy_mailingu['PL'],'Marketing ASGARD',
            # 'marketing@asgard.gifts',dane_mailing['adres_strony_mailingu'],data_wyslania)
            # wyslij_do_handlowcow_redlink(dane_mailing['nazwa_mailingu'],dane_mailing['temat_PL'],'Marketing ASGARD',
            # 'marketing@asgard.gifts',dane_mailing['adres_strony_mailingu'],data_wyslania)

            KampaniaRedlink.objects.create(nazwa_kampanii=nazwa_mailingu, kiedy_wyslany=data_wyslania,
                                           temat_mailingu_pl=tematy_mailingu['PL'],
                                           temat_mailingu_en=tematy_mailingu['EN'],
                                           temat_mailingu_de=tematy_mailingu['DE'],
                                           temat_mailingu_fr=tematy_mailingu['FR'],
                                           link_content=adres_strony_mailingu, ctr_pl=0, open_rate_pl=0, ctr_en=0,
                                           open_rate_en=0, ctr_de=0, open_rate_de=0, ctr_fr=0, open_rate_fr=0,
                                           dostarczone_wiadomoscidostarczone_wiadomosci_pl=0,
                                           dostarczone_wiadomoscidostarczone_wiadomosci_en=0,
                                           dostarczone_wiadomoscidostarczone_wiadomosci_de=0,
                                           dostarczone_wiadomoscidostarczone_wiadomosci_fr=0,
                                           un_sub_pl=0, un_sub_en=0, un_sub_de=0, un_sub_fr=0)

            lista_grup_redlink = show_all_grups()

            for jezyk in lista_jezykow:
                if len(tematy_mailingu[jezyk]) > 1:
                    temat=tematy_mailingu[jezyk]
                    adres_strony_mailingu = adres_strony_mailingu.split('_')[0]
                    content_mailingu = f'{adres_strony_mailingu}_{jezyk.lower()}.html'
                    for itemRedlink in lista_grup_redlink:
                        grup_id = itemRedlink['GroupId']
                        if itemRedlink['GroupName'].endswith(f'{jezyk}'):
                            imie = re.findall(r'(^[A-Z][a-z]*)', itemRedlink['GroupName'].split('_')[0])[0]
                            nazwisko = re.findall(r'([A-Z][a-z]*$)', itemRedlink['GroupName'].split('_')[0])[0]
                            mail_wysylki = f'{imie[0].lower()}.{nazwisko.lower()}@asgard.gifts'
                            imie_nazwisko_handlowca = f'{imie} {nazwisko}'
                            # id_kampanii = wyslij_mailing_redlink(nazwa_mailingu, temat, imie_nazwisko, mail_wysylki,
                            #                                      content_mailingu, data_wyslania, grup_id)
                            id_kampanii = '2B872BAF-B1DC-4562-A3E7-52ADAA3D401D'
                            # utworzenie rekordu z danymi handlowca powiązanego z kompanią
                            Handlowiec.objects.create(redlink_id=id_kampanii, jezyk=jezyk.lower(), ctr=0, open_rate=0,
                                                      dostarczone_wiadomosci=0, un_sub=0, imie_nazwisko=imie_nazwisko_handlowca,
                                                      nazwa_kampanii=nazwa_mailingu)
                else:
                    grup_id = itemRedlink['GroupId']
                    if itemRedlink['GroupName'].endswith(f'{jezyk}'):
                        imie = re.findall(r'(^[A-Z][a-z]*)', itemRedlink['GroupName'].split('_')[0])[0]
                        nazwisko = re.findall(r'([A-Z][a-z]*$)', itemRedlink['GroupName'].split('_')[0])[0]
                        mail_wysylki = f'{imie[0].lower()}.{nazwisko.lower()}@asgard.gifts'
                        imie_nazwisko_handlowca = f'{imie} {nazwisko}'
                        # utworzenie rekordu z danymi handlowca powiązanego z kompanią
                        Handlowiec.objects.create(redlink_id= 0, jezyk=jezyk.lower(), ctr=0, open_rate=0,
                                                  dostarczone_wiadomosci=0, un_sub=0,
                                                  imie_nazwisko=imie_nazwisko_handlowca)

            print('WYSYLKA ZAKONCZONA')

            return redirect('http://127.0.0.1:8000/')