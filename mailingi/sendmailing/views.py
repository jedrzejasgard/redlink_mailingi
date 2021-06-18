
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import KampaniaRedlink, Handlowiec
import pandas as pd
import configparser
import zeep
import datetime
import json
import re

config = configparser.ConfigParser()
configFilePath = 'C:/Users/asgard_48/Documents/Skrypty/BAZA TESTOWA - WGRYWANIE WD/baza mail/redlink.ini'
config.read(configFilePath)

usr = config.get('redlink', 'redlink_API_user')
passw = config.get('redlink', 'redlink_API_pass')


def wyslijmailingReg(request):
    return render(request, 'wyslijmailing.html')

def wyslijmailingVip(request):
    lista_grup_redlink_handlowcy = show_all_grups()
    listymailingoweVIP = []
    for itemRedlink in lista_grup_redlink_handlowcy:
        grup_id = itemRedlink['GroupId']
        if itemRedlink['GroupName'].startswith('VIP'):
            imie = re.findall(r'(^[A-Z][a-z]*)', itemRedlink['GroupName'].split('_')[1])[0]
            nazwisko = re.findall(r'([A-Z][a-z]*$)', itemRedlink['GroupName'].split('_')[1])[0]
            jezyk = itemRedlink['GroupName'].split('_')[-1]
            imie_nazwisko_handlowca = f'{imie} {nazwisko} {jezyk}'
            listymailingoweVIP.append(imie_nazwisko_handlowca)
        else:
            pass

    return render(request, 'wyslijmailingVip.html', {'listymailingowe': listymailingoweVIP})

def landing(request):
    return render(request, 'landing.html')

def blad_nazwy(request):
    return render(request, 'blad_nazwy.html')


def zestawienie_kampanii(request):
    kampanie_model = KampaniaRedlink.objects.all().values()
    return render(request, 'zestawienie_kampanii.html', {'kampanie': kampanie_model})

# pobieranie informacji z API REDLINK szczegółowych o każdej grupie mailingowej danego handlowca
def szczegoly_kampanii_redlink(id_kampanii, data_wyslania):
    data_do = data_wyslania.split('-')
    data_do[-1] = str(int(data_do[-1])+2)
    if len(data_do[-1]) <= 1:
        data_do[-1] = '0'+data_do[-1]
    data_do = '-'.join(data_do)
    try:
        redlink_kampania = zeep.Client('https://redlink.pl/ws/v1/Soap/MailCampaigns/MailCampaigns.asmx?WSDL')
        client = zeep.Client('https://redlink.pl/ws/v1/Soap/Contacts/Groups.asmx?WSDL')
        response_bounce = redlink_kampania.service.GetMailCampaignBouncesReport(strUserName=usr,
                                                                                strPassword=passw,
                                                                                strCampaignId=id_kampanii,
                                                                                dateFrom=str(data_wyslania),
                                                                                dateTo=data_do,
                                                                                offset=0,
                                                                                limit=10000)
        response_ctr = redlink_kampania.service.GetMailCampaignCtrReport(strUserName=usr,
                                                                         strPassword=passw,
                                                                         strCampaignId=id_kampanii,
                                                                         dateFrom=str(data_wyslania),
                                                                         dateTo=data_do,
                                                                         offset=0,
                                                                         limit=10000)
        response_data = redlink_kampania.service.GetMailCampaignData(strUserName=usr,
                                                                     strPassword=passw,
                                                                     strCampaignId=id_kampanii)
        response_or = redlink_kampania.service.GetMailCampaignOrReport(strUserName=usr,
                                                                       strPassword=passw,
                                                                       strCampaignId=id_kampanii,
                                                                       dateFrom=str(data_wyslania),
                                                                       dateTo=data_do,
                                                                       offset=0,
                                                                       limit=10000)
        response_unsub = redlink_kampania.service.GetMailCampaignUnregistrationsReport(strUserName=usr,
                                                                                       strPassword=passw,
                                                                                       strCampaignId=id_kampanii,
                                                                                       dateFrom=str(data_wyslania),
                                                                                       dateTo=data_do,
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
        print(f'r_json_groupcount: {r_json_groupcount}')
        r_json_unsub = zeep.helpers.serialize_object(response_unsub)
        print(f'r_json_unsub: {r_json_unsub}')
        try:
            un_sub = len(r_json_unsub['Results'])
        except:
            un_sub = 0
        clicks = 0
        for item in r_json_ctr['Results']['MailCampaignCtrData']:
            clicks += int(item['Count'])
        print(f'Clicks: {clicks}')
        bounces = len(r_json_bounce['Results']['MailCampaignBounceData'])
        print(f'BO: {bounces}' )
        otwarte_maile = len(r_json_or['Results']['MailCampaignOrData'])
        print(f'Otwarte: {otwarte_maile}')
        dostarczone_wiadomosci = int(r_json_groupcount['Data']) - int(bounces)
        print(f'otwarta: {dostarczone_wiadomosci}, BO {bounces}' )
        ctr = round(clicks*100/dostarczone_wiadomosci, 2)
        open_rate = round(otwarte_maile*100/dostarczone_wiadomosci, 2)
        dane = [ctr, open_rate, dostarczone_wiadomosci, un_sub, clicks, dostarczone_wiadomosci, otwarte_maile, bounces]
    except:
        dane = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    print(dane)
    return dane


def detale_kampanii(request):
    if request.method == "POST":
        id_kampanii = (request.POST['form_id_kampanii_detale']).split('_')[1]
        kampanie_model = KampaniaRedlink.objects.filter(id=str(id_kampanii)).values()
        nazwa_kampanii = kampanie_model[0]['nazwa_kampanii']
        handlowcy_kampanii = Handlowiec.objects.filter(nazwa_kampanii=nazwa_kampanii).values()

        data_wyslania = str(kampanie_model[0]['kiedy_wyslany'].split(' ')[0])
        data_sprawdzenia = data_wyslania.split('-')
        data_sprawdzenia[-1] = str(int(data_sprawdzenia[-1]) + 2)
        if len(data_sprawdzenia[-1]) <= 1:
            data_sprawdzenia[-1] = '0' + data_sprawdzenia[-1]
        data_sprawdzenia = '-'.join(data_sprawdzenia)
        dzisiaj = str(datetime.date.today())
        if data_sprawdzenia > dzisiaj:
            print('sprawdzam dane')

        # data_wyslania = '2021-03-01'

            wyniki_handlowcy_pl = {}
            wyniki_handlowcy_en = {}
            wyniki_handlowcy_de = {}
            wyniki_handlowcy_fr = {}
            dostarczone_wiadomosci_pl = 0
            dostarczone_wiadomosci_en = 0
            dostarczone_wiadomosci_de = 0
            dostarczone_wiadomosci_fr = 0
            un_sub_pl = 0
            un_sub_en = 0
            un_sub_de = 0
            un_sub_fr = 0
            clicks_pl = 0
            clicks_en = 0
            clicks_de = 0
            clicks_fr = 0
            opens_pl = 0
            opens_en = 0
            opens_de = 0
            opens_fr = 0
            hb_pl = 0
            hb_en = 0
            hb_de = 0
            hb_fr = 0
            for handlowiec in handlowcy_kampanii:
                id_redlink = handlowiec['redlink_id']
                if handlowiec['jezyk'] == 'pl':
                    wyniki_handlowcy_pl[handlowiec['imie_nazwisko']] = (id_redlink, szczegoly_kampanii_redlink(id_redlink, data_wyslania))
                elif handlowiec['jezyk'] == 'en':
                    wyniki_handlowcy_en[handlowiec['imie_nazwisko']] = (id_redlink, szczegoly_kampanii_redlink(id_redlink, data_wyslania))
                elif handlowiec['jezyk'] == 'de':
                    wyniki_handlowcy_de[handlowiec['imie_nazwisko']] = (id_redlink, szczegoly_kampanii_redlink(id_redlink, data_wyslania))
                elif handlowiec['jezyk'] == 'fr':
                    wyniki_handlowcy_fr[handlowiec['imie_nazwisko']] = (id_redlink, szczegoly_kampanii_redlink(id_redlink, data_wyslania))
            for handlowiec in wyniki_handlowcy_pl:
                handlowiec = wyniki_handlowcy_pl[handlowiec][1]
                un_sub_pl += int(handlowiec[3])
                clicks_pl += int(handlowiec[4])
                dostarczone_wiadomosci_pl += int(handlowiec[5])
                opens_pl += int(handlowiec[6])
                hb_pl += int(handlowiec[7])
            ctr_pl = round(clicks_pl * 100 / dostarczone_wiadomosci_pl, 2)
            open_rate_pl = round(opens_pl * 100 / dostarczone_wiadomosci_pl, 2)
            for handlowiec in wyniki_handlowcy_en:
                handlowiec = wyniki_handlowcy_en[handlowiec][1]
                un_sub_en += int(handlowiec[3])
                clicks_en += int(handlowiec[4])
                dostarczone_wiadomosci_en += int(handlowiec[5])
                opens_en += int(handlowiec[6])
                hb_en += int(handlowiec[7])
            ctr_en = round(clicks_en * 100 / dostarczone_wiadomosci_en, 2)
            open_rate_en = round(opens_en * 100 / dostarczone_wiadomosci_en, 2)
            for handlowiec in wyniki_handlowcy_de:
                handlowiec = wyniki_handlowcy_de[handlowiec][1]
                un_sub_de += int(handlowiec[3])
                clicks_de += int(handlowiec[4])
                dostarczone_wiadomosci_de += int(handlowiec[5])
                opens_de += int(handlowiec[6])
                hb_de += int(handlowiec[7])
            ctr_de = round(clicks_pl * 100 / dostarczone_wiadomosci_de, 2)
            open_rate_de = round(opens_de * 100 / dostarczone_wiadomosci_de, 2)
            for handlowiec in wyniki_handlowcy_fr:
                handlowiec = wyniki_handlowcy_fr[handlowiec][1]
                un_sub_fr += handlowiec[3]
                clicks_fr += handlowiec[4]
                dostarczone_wiadomosci_fr += handlowiec[5]
                opens_fr += handlowiec[6]
                hb_fr += handlowiec[7]
            ctr_fr = round(clicks_fr * 100 / dostarczone_wiadomosci_fr, 2)
            open_rate_fr = round(opens_fr * 100 / dostarczone_wiadomosci_fr, 2)
            kampania_model = KampaniaRedlink.objects.get(id=str(id_kampanii))
            kampania_model.ctr_pl = ctr_pl
            kampania_model.ctr_en = ctr_en
            kampania_model.ctr_de = ctr_de
            kampania_model.ctr_fr = ctr_fr
            kampania_model.open_rate_pl = open_rate_pl
            kampania_model.open_rate_en = open_rate_en
            kampania_model.open_rate_de = open_rate_de
            kampania_model.open_rate_fr = open_rate_fr
            kampania_model.dostarczone_wiadomosci_pl = dostarczone_wiadomosci_pl
            kampania_model.dostarczone_wiadomosci_en = dostarczone_wiadomosci_en
            kampania_model.dostarczone_wiadomosci_de = dostarczone_wiadomosci_de
            kampania_model.dostarczone_wiadomosci_fr = dostarczone_wiadomosci_fr
            kampania_model.un_sub_pl = un_sub_pl
            kampania_model.un_sub_en = un_sub_en
            kampania_model.un_sub_de = un_sub_de
            kampania_model.un_sub_fr = un_sub_fr
            kampania_model.hard_bounces_pl = hb_pl
            kampania_model.hard_bounces_en = hb_en
            kampania_model.hard_bounces_de = hb_de
            kampania_model.hard_bounces_fr = hb_fr
            kampania_model.save(update_fields=['ctr_pl', 'ctr_en', 'ctr_de', 'ctr_fr', 'open_rate_pl', 'open_rate_en',
                                               'open_rate_de', 'open_rate_fr','dostarczone_wiadomosci_pl',
                                               'dostarczone_wiadomosci_en', 'dostarczone_wiadomosci_de',
                                               'dostarczone_wiadomosci_fr', 'un_sub_pl', 'un_sub_en', 'un_sub_de',
                                               'un_sub_fr', 'hard_bounces_pl', 'hard_bounces_en', 'hard_bounces_de',
                                               'hard_bounces_fr'])
        else:
            wyniki_handlowcy_pl = {}
            wyniki_handlowcy_en = {}
            wyniki_handlowcy_de = {}
            wyniki_handlowcy_fr = {}
            dostarczone_wiadomosci_pl = 0
            dostarczone_wiadomosci_en = 0
            dostarczone_wiadomosci_de = 0
            dostarczone_wiadomosci_fr = 0
            un_sub_pl = 0
            un_sub_en = 0
            un_sub_de = 0
            un_sub_fr = 0
            clicks_pl = 0
            clicks_en = 0
            clicks_de = 0
            clicks_fr = 0
            opens_pl = 0
            opens_en = 0
            opens_de = 0
            opens_fr = 0
            hb_pl = 0
            hb_en = 0
            hb_de = 0
            hb_fr = 0
            for handlowiec in handlowcy_kampanii:
                id_redlink = handlowiec['redlink_id']
                if handlowiec['jezyk'] == 'pl':
                    wyniki_handlowcy_pl[handlowiec['imie_nazwisko']] = (id_redlink, szczegoly_kampanii_redlink(id_redlink, data_wyslania))
                elif handlowiec['jezyk'] == 'en':
                    wyniki_handlowcy_en[handlowiec['imie_nazwisko']] = (id_redlink, szczegoly_kampanii_redlink(id_redlink, data_wyslania))
                elif handlowiec['jezyk'] == 'de':
                    wyniki_handlowcy_de[handlowiec['imie_nazwisko']] = (id_redlink, szczegoly_kampanii_redlink(id_redlink, data_wyslania))
                elif handlowiec['jezyk'] == 'fr':
                    wyniki_handlowcy_fr[handlowiec['imie_nazwisko']] = (id_redlink, szczegoly_kampanii_redlink(id_redlink, data_wyslania))
            for handlowiec in wyniki_handlowcy_pl:
                handlowiec = wyniki_handlowcy_pl[handlowiec][1]
                un_sub_pl += int(handlowiec[3])
                clicks_pl += int(handlowiec[4])
                dostarczone_wiadomosci_pl += int(handlowiec[5])
                opens_pl += int(handlowiec[6])
                hb_pl += int(handlowiec[7])
            ctr_pl = round(clicks_pl * 100 / dostarczone_wiadomosci_pl, 2)
            open_rate_pl = round(opens_pl * 100 / dostarczone_wiadomosci_pl, 2)
            for handlowiec in wyniki_handlowcy_en:
                handlowiec = wyniki_handlowcy_en[handlowiec][1]
                un_sub_en += int(handlowiec[3])
                clicks_en += int(handlowiec[4])
                dostarczone_wiadomosci_en += int(handlowiec[5])
                opens_en += int(handlowiec[6])
                hb_en += int(handlowiec[7])
            ctr_en = round(clicks_en * 100 / dostarczone_wiadomosci_en, 2)
            open_rate_en = round(opens_en * 100 / dostarczone_wiadomosci_en, 2)
            for handlowiec in wyniki_handlowcy_de:
                handlowiec = wyniki_handlowcy_de[handlowiec][1]
                un_sub_de += int(handlowiec[3])
                clicks_de += int(handlowiec[4])
                dostarczone_wiadomosci_de += int(handlowiec[5])
                opens_de += int(handlowiec[6])
                hb_de += int(handlowiec[7])
            ctr_de = round(clicks_pl * 100 / dostarczone_wiadomosci_de, 2)
            open_rate_de = round(opens_de * 100 / dostarczone_wiadomosci_de, 2)
            for handlowiec in wyniki_handlowcy_fr:
                handlowiec = wyniki_handlowcy_fr[handlowiec][1]
                un_sub_fr += handlowiec[3]
                clicks_fr += handlowiec[4]
                dostarczone_wiadomosci_fr += handlowiec[5]
                opens_fr += handlowiec[6]
                hb_fr += handlowiec[7]
            ctr_fr = round(clicks_fr * 100 / dostarczone_wiadomosci_fr, 2)
            open_rate_fr = round(opens_fr * 100 / dostarczone_wiadomosci_fr, 2)
            kampania_model = KampaniaRedlink.objects.get(id=str(id_kampanii))
            kampania_model.ctr_pl = ctr_pl
            kampania_model.ctr_en = ctr_en
            kampania_model.ctr_de = ctr_de
            kampania_model.ctr_fr = ctr_fr
            kampania_model.open_rate_pl = open_rate_pl
            kampania_model.open_rate_en = open_rate_en
            kampania_model.open_rate_de = open_rate_de
            kampania_model.open_rate_fr = open_rate_fr
            kampania_model.dostarczone_wiadomosci_pl = dostarczone_wiadomosci_pl
            kampania_model.dostarczone_wiadomosci_en = dostarczone_wiadomosci_en
            kampania_model.dostarczone_wiadomosci_de = dostarczone_wiadomosci_de
            kampania_model.dostarczone_wiadomosci_fr = dostarczone_wiadomosci_fr
            kampania_model.un_sub_pl = un_sub_pl
            kampania_model.un_sub_en = un_sub_en
            kampania_model.un_sub_de = un_sub_de
            kampania_model.un_sub_fr = un_sub_fr
            kampania_model.hard_bounces_pl = hb_pl
            kampania_model.hard_bounces_en = hb_en
            kampania_model.hard_bounces_de = hb_de
            kampania_model.hard_bounces_fr = hb_fr
            kampania_model.save(update_fields=['ctr_pl', 'ctr_en', 'ctr_de', 'ctr_fr', 'open_rate_pl', 'open_rate_en',
                                               'open_rate_de', 'open_rate_fr','dostarczone_wiadomosci_pl',
                                               'dostarczone_wiadomosci_en', 'dostarczone_wiadomosci_de',
                                               'dostarczone_wiadomosci_fr', 'un_sub_pl', 'un_sub_en', 'un_sub_de',
                                               'un_sub_fr', 'hard_bounces_pl', 'hard_bounces_en', 'hard_bounces_de',
                                               'hard_bounces_fr'])

    return render(request, 'detale_kampanii.html', {'szczegoly': kampanie_model,
                                                    'handlowcy_pl': wyniki_handlowcy_pl,
                                                    'handlowcy_en': wyniki_handlowcy_en,
                                                    'handlowcy_de': wyniki_handlowcy_de,
                                                    'handlowcy_fr': wyniki_handlowcy_fr})


def wyslij_test_redlink(nazwa_mailingu, temat, imie_nazwisko, mail_wysylki, content_mailingu):
    mail = zeep.Client("https://redlink.pl/ws/v1/Soap/MailCampaigns/MailCampaigns.asmx?WSDL")
    data = {'Name': nazwa_mailingu, 'Subject': '   TEST   ' + temat, 'FromName': imie_nazwisko,
            'FromAddress': mail_wysylki, 'HtmlFromWebSiteUrl': content_mailingu,
            'GroupId': '66F3AE43-6DDC-475E-8DB6-6775EBF9030D', 'TrackLinks': True}
    response = mail.service.CreateMailCampaign(strUserName=usr, strPassword=passw, data=data)
    r_json = zeep.helpers.serialize_object(response)
    print(r_json)


def wyslij_VIP_redlink(nazwa_mailingu, temat, imie_nazwisko, mail_wysylki, content_mailingu,data_wyslania,grup_id):
    print('Wysyłam dane do redlinka')
    mail = zeep.Client("https://redlink.pl/ws/v1/Soap/MailCampaigns/MailCampaigns.asmx?WSDL")
    data = {'Name': nazwa_mailingu,
            'Subject': temat,
            'FromName': imie_nazwisko,
            'FromAddress': mail_wysylki,
            'HtmlContent': content_mailingu,
            'GroupId': grup_id,
            'ScheduleTime': data_wyslania,
            'TrackLinks': True}

    response = mail.service.CreateMailCampaign(strUserName=usr, strPassword=passw, data=data)
    r_json = zeep.helpers.serialize_object(response)
    print(r_json)


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


def wyslij_do_asgardian_redlink(nazwa_mailingu, temat, imie_nazwisko, mail_wysylki,content_mailingu,data_wyslania):
    mail = zeep.Client("https://redlink.pl/ws/v1/Soap/MailCampaigns/MailCampaigns.asmx?WSDL")
    data = {'Name': nazwa_mailingu, 'Subject': temat, 'FromName': imie_nazwisko, 'FromAddress': mail_wysylki,
            'HtmlFromWebSiteUrl': content_mailingu, 'GroupId': '28514C29-8294-41F6-82EB-0E1335B8C5B1',
            'ScheduleTime': data_wyslania, 'TrackLinks': True}
    response = mail.service.CreateMailCampaign(strUserName=usr, strPassword=passw, data = data)
    r_json = zeep.helpers.serialize_object(response)


def wyslij_do_handlowcow_redlink(nazwa_mailingu, temat, imie_nazwisko, mail_wysylki,content_mailingu,data_wyslania):
    mail = zeep.Client("https://redlink.pl/ws/v1/Soap/MailCampaigns/MailCampaigns.asmx?WSDL")
    data = {'Name': nazwa_mailingu, 'Subject': f'Wysyłka: {data_wyslania}, Temat: {temat}', 'FromName': imie_nazwisko,
            'FromAddress': mail_wysylki, 'HtmlFromWebSiteUrl': content_mailingu,
            'GroupId': 'FAE0FBDB-67E7-47A4-BA0E-7D4C3E650639', 'TrackLinks': True}
    response =  mail.service.CreateMailCampaign(strUserName=usr, strPassword=passw, data = data)
    r_json = zeep.helpers.serialize_object(response)


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

            wyslij_do_asgardian_redlink(dane_mailing['nazwa_mailingu'], tematy_mailingu['PL'], 'Marketing ASGARD',
                                        'marketing@asgard.gifts', dane_mailing['adres_strony_mailingu'], data_wyslania)
            wyslij_do_handlowcow_redlink(dane_mailing['nazwa_mailingu'], dane_mailing['temat_PL'],'Marketing ASGARD',
                                         'marketing@asgard.gifts', dane_mailing['adres_strony_mailingu'], data_wyslania)

            KampaniaRedlink.objects.create(nazwa_kampanii=nazwa_mailingu, kiedy_wyslany=data_wyslania,
                                           temat_mailingu_pl=tematy_mailingu['PL'],
                                           temat_mailingu_en=tematy_mailingu['EN'],
                                           temat_mailingu_de=tematy_mailingu['DE'],
                                           temat_mailingu_fr=tematy_mailingu['FR'],
                                           link_content=adres_strony_mailingu, ctr_pl=0, open_rate_pl=0, ctr_en=0,
                                           open_rate_en=0, ctr_de=0, open_rate_de=0, ctr_fr=0, open_rate_fr=0,
                                           dostarczone_wiadomosci_pl=0,
                                           dostarczone_wiadomosci_en=0,
                                           dostarczone_wiadomosci_de=0,
                                           dostarczone_wiadomosci_fr=0,
                                           un_sub_pl=0, un_sub_en=0, un_sub_de=0, un_sub_fr=0)

            lista_grup_redlink_handlowcy = show_all_grups()
            #print(lista_grup_redlink_handlowcy)
            for jezyk in lista_jezykow:
                if len(tematy_mailingu[jezyk]) > 1:
                    temat=tematy_mailingu[jezyk]
                    adres_strony_mailingu = adres_strony_mailingu.split('_')[0]
                    content_mailingu = f'{adres_strony_mailingu}_{jezyk.lower()}.html'
                    for itemRedlink in lista_grup_redlink_handlowcy:
                        grup_id = itemRedlink['GroupId']
                        if itemRedlink['GroupName'].endswith(f'{jezyk}') and not itemRedlink['GroupName'].startswith('VIP'):
                            #itemRedlink = itemRedlink['GroupName'].replace('VIP_','')
                            imie = re.findall(r'(^[A-Z][a-z]*)', itemRedlink['GroupName'].split('_')[0])[0]
                            nazwisko = re.findall(r'([A-Z][a-z]*$)', itemRedlink['GroupName'].split('_')[0])[0]
                            mail_wysylki = f'{imie[0].lower()}.{nazwisko.lower()}@asgard.gifts'
                            imie_nazwisko_handlowca = f'{imie} {nazwisko}'
                            print(imie_nazwisko_handlowca)
                            id_kampanii = wyslij_mailing_redlink(nazwa_mailingu, temat, imie_nazwisko_handlowca, mail_wysylki,
                                                                 content_mailingu, data_wyslania, grup_id)
                            # id_kampanii = '2B872BAF-B1DC-4562-A3E7-52ADAA3D401D'
                            # utworzenie rekordu z danymi handlowca powiązanego z kompanią
                            Handlowiec.objects.create(redlink_id=id_kampanii, jezyk=jezyk.lower(), ctr=0, open_rate=0,
                                                      dostarczone_wiadomosci=0, un_sub=0, imie_nazwisko=imie_nazwisko_handlowca,
                                                      nazwa_kampanii=nazwa_mailingu)
                else:
                    for itemRedlink in lista_grup_redlink_handlowcy:
                        grup_id = itemRedlink['GroupId']
                        if itemRedlink['GroupName'].endswith(f'{jezyk}'):
                            imie = re.findall(r'(^[A-Z][a-z]*)', itemRedlink['GroupName'].split('_')[0])[0]
                            nazwisko = re.findall(r'([A-Z][a-z]*$)', itemRedlink['GroupName'].split('_')[0])[0]
                            mail_wysylki = f'{imie[0].lower()}.{nazwisko.lower()}@asgard.gifts'
                            imie_nazwisko_handlowca = f'{imie} {nazwisko}'
                            # utworzenie rekordu z danymi handlowca powiązanego z kompanią
                            Handlowiec.objects.create(redlink_id= grup_id, jezyk=jezyk.lower(), ctr=0, open_rate=0,
                                                      dostarczone_wiadomosci=0, un_sub=0,
                                                      imie_nazwisko=imie_nazwisko_handlowca)

            print('WYSYLKA ZAKONCZONA')

            return redirect('http://127.0.0.1:8000/')


def generuj_stats(request):
    if request.method == 'POST':
        id_kampanii = (request.POST['form_id_kampanii_generuj']).split('_')[1]
        print(id_kampanii)
        kampanie_model = KampaniaRedlink.objects.filter(id=str(id_kampanii)).values()
        nazwa_kampanii = kampanie_model[0]['nazwa_kampanii']
        df = pd.DataFrame({'Jezyk': [f'{nazwa_kampanii}', 'PL', 'EN', 'DE', 'FR'],
                           'Dostarczone': ['', kampanie_model[0]['dostarczone_wiadomosci_pl'],
                                           kampanie_model[0]['dostarczone_wiadomosci_en'],
                                           kampanie_model[0]['dostarczone_wiadomosci_de'],
                                           kampanie_model[0]['dostarczone_wiadomosci_fr']],
                           'HB': ['', kampanie_model[0]['hard_bounces_pl'],
                                           kampanie_model[0]['hard_bounces_en'],
                                           kampanie_model[0]['hard_bounces_de'],
                                           kampanie_model[0]['hard_bounces_fr']],
                           'CTR': ['', kampanie_model[0]['ctr_pl'],
                                           kampanie_model[0]['ctr_en'],
                                           kampanie_model[0]['ctr_de'],
                                           kampanie_model[0]['ctr_fr']],
                           'OR': ['', kampanie_model[0]['open_rate_pl'],
                                           kampanie_model[0]['open_rate_en'],
                                           kampanie_model[0]['open_rate_de'],
                                           kampanie_model[0]['open_rate_fr']],
                           'UnSub': ['', kampanie_model[0]['un_sub_pl'],
                                           kampanie_model[0]['un_sub_en'],
                                           kampanie_model[0]['un_sub_de'],
                                           kampanie_model[0]['un_sub_fr']]
                           })
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="zestawienie_kampanii.xlsx"'
        df.to_excel(response)
        return response

def wyslij_mailing_vip(request):
    if request.method == 'POST':
        lista_grup_redlink_handlowcy = show_all_grups()
        print(lista_grup_redlink_handlowcy)
        dane_mailing_post = request.POST['formMailing']
        dane_mailing = json.loads(dane_mailing_post)
        print(dane_mailing)
        nazwa_mailingu = dane_mailing['nazwa_mailingu']
        data_wysylki_input = dane_mailing['data_wysylki_input'].replace(':', '-')
        year, month, day, hour, minute, second = map(int, data_wysylki_input.split('-'))
        data_wyslania = datetime.datetime(year, month, day, hour, minute, second)

        try:
            print(KampaniaRedlink.objects.filter(nazwa_kampanii=nazwa_mailingu).values())
            len(KampaniaRedlink.objects.filter(nazwa_kampanii=nazwa_mailingu).values()[0])
            return redirect('http://127.0.0.1:8000/blad_nazwy')
        except:
            print('wysyłam nowy mailing')

        KampaniaRedlink.objects.create(nazwa_kampanii=nazwa_mailingu, kiedy_wyslany=data_wyslania,
                                       temat_mailingu_pl=dane_mailing['PL-temat'],
                                       temat_mailingu_en=dane_mailing['EN-temat'],
                                       temat_mailingu_de=dane_mailing['DE-temat'],
                                       temat_mailingu_fr=dane_mailing['FR-temat'],
                                       link_content= 'szblon newsletera', ctr_pl=0, open_rate_pl=0, ctr_en=0,
                                       open_rate_en=0, ctr_de=0, open_rate_de=0, ctr_fr=0, open_rate_fr=0,
                                       dostarczone_wiadomosci_pl=0,
                                       dostarczone_wiadomosci_en=0,
                                       dostarczone_wiadomosci_de=0,
                                       dostarczone_wiadomosci_fr=0,
                                       un_sub_pl=0, un_sub_en=0, un_sub_de=0, un_sub_fr=0)

        for handlowiec in dane_mailing['wysylka_do']:
            print(handlowiec)
            item_handlowiec = handlowiec.split(' ')
            imie_nazwisko_handlowca = ' '.join(item_handlowiec[:2])
            imie = item_handlowiec[0]
            nazwisko = item_handlowiec[1]
            jezyk = item_handlowiec[2]
            mail_wysylki = imie[0].lower() + '.' + nazwisko.lower() + '@asgard.gifts'
            handlowcy_numery_tel = {
                'KLUSZCZYNSKA': '61 844 24 20',
                'SITEK': '61 844 24 22',
                'PISZCZOLA': '61 844 24 21',
                'IDZIAK': '61 844 24 23',
                'MIKOLAJCZYK': '61 844 24 24',
                'URBANCZYK': '61 844 24 25',
                'NIEGLOS': '61 844 24 09',
                'MUSZYNSKA': '61 844 24 33',
                'PRANGE': '61 842 87 74',
                'BUJAKOWSKA': '61 842 87 72',
                'STRZELECKI': '61 842 87 75',
                'MALGORZATA': '61 844 24 13',
                'TRAFNA': '61 844 24 07',
                'PAWLEWSKI': '0000000000',
            }
            numer_tel = handlowcy_numery_tel[nazwisko.upper()]
            if jezyk == 'PL':
                pl_temat = dane_mailing['PL-temat']
                pl_termin = dane_mailing['PL-termin']
                pl_yt = dane_mailing['PL-yt']
                pl_prezentacja = dane_mailing['PL-prezentacja']
                temat = pl_temat
                content_mailingu = f"""
                                <html>
                                <head>                          
                                  <meta http-equiv="content-type" content="text/html; charset=UTF-8">
                                </head>
                                <body>  
                                    <div style="padding: 100px;">
                                        <p>Drogi kliencie,</p>
                                        <p>Pewnie pamiętasz, ale pozwolę sobie Ci przypomnieć, że jesteś w wąskiej grupie naszych najlepszych klientów. W związku z tym ponownie mam przyjemność zaprezentować Ci z przedpremierowo nowości, które co miesiąc wprowadzamy do naszej oferty w ramach serii Fantastic5. </p>
                                        <p>Oto i on. <strong> Nasz najnowszy film z cyklu Fantastic5 prezentujący zestaw produktów, których oficjalna premiera nastąpi dopiero za tydzień!</strong> </p>
                                        <p><strong>Zobacz go już dzisiaj klikając w ten link:</strong> <a href="{pl_yt}">LINK</a> </p>
                                        <p>Prezentację przedstawionych produktów w formie pdf możesz przejrzeć klikając tutaj:  <a href="{pl_prezentacja}">CLICK</a> </p>
                                        <p>Najczęściej zadawane pytania dotyczące Fantastic5 zgromadziliśmy tutaj: <a href="https://asgard.gifts/kategoria/najczesciej-zadawane-pytania_263_1.html">CLICK</a> </p>
                                        <p>Dotychczas wprowadzone serie produktów z cyklu Fantastic5 możesz obejrzeć tutaj: <a href="https://asgard.gifts/kategoria/nowosci-fantastic-5_262_1.html"> CLICK</a> </p>
                                        <p>Ale to nie wszystko!</p>
                                        <p><strong>Zapraszam Cię również na indywidualną prezentację</strong> produktów przeprowadzoną przeze mnie wyłącznie dla Ciebie. Jeśli masz ochotę, daj mi znać, a ustalimy dogodny dla Ciebie termin.</p>
                                        <p>Zaprezentowane powyżej produkty zostaną  dodane do naszej oferty <strong>{pl_termin}</strong> . Tego dnia pojawią się w naszym sklepie internetowym. </p>
                                        <p>W dniu ich oficjalnej premiery otrzymasz ode mnie również dodatkowy e-mail ze szczegółami nowej oferty, opcją integracji ze swoją ofertą oraz materiałami, które możesz przesłać swoim klientom.</p>
                                      </div>                            
                                    <table colspan="0" style="border-collapse: collapse;
                                      border-spacing: 0px; margin-top: 10px; color: black;"
                                      cellspacing="0" cellpadding="0">
                                      <tbody>                                    
                                        <tr>
                                          <td>
                                              
                                          </td>
                                        </tr>
                                        <tr>
                                          <td style="height: 150px; ">
                                            <table style="vertical-align: top; border-collapse:
                                              collapse; border-spacing: 0px; background-color:
                                              #f2f2f2; height: 150px;" cellspacing="0" cellpadding="0">
                                              <tbody>
                                                <tr>
                                                  <td style="height: 20px; width:20px; padding: 0px;
                                                    vertical-align: top;"><br>
                                                  </td>
                                                  <td style="display: block; width: 140px;">
                                                    <p style="margin-bottom: 5px; font-size: 15px;
                                                      margin-top: 20px;"><b>{imie}<br>{nazwisko}</b></p>
                                                    <p style="font-size: 9px; margin-top: 5px;">SPECJALISTA DS. HANDLOWYCH</p>
                                                    <table>
                                                      <tbody>
                                                        <tr>
                                                          <td style="font-size: 13px;"><b>{numer_tel}</b></td>
                                                        </tr>
                                                        <tr>
                                                          <td style="font-size: 11px;"><b><a
                                                                style="color: black; text-decoration:
                                                                none;" href="http://www.asgard.gifts">www.asgard.gifts</a></b></td>
                                                        </tr>
                                                      </tbody>
                                                    </table>
                                                  </td>
                                                  <td style="height: 20px; width:20px; padding: 0px;
                                                    vertical-align: top;"> <br>
                                                  </td>
                                                </tr>
                                              </tbody>
                                            </table>
                                          </td>
                                          <td style="padding: 1px; background-color: #ff7300; height:
                                            145px;"> <br>
                                          </td>
                                          <td style="padding: 5px; height: 145px;"> <br>
                                          </td>
                                          <td height="150px">
                                            <table style="vertical-align: top; border-collapse:
                                              collapse; border-spacing: 0px; background-color:
                                              #f2f2f2; height: 150px;" cellspacing="0" cellpadding="0"
                                              height="150">
                                              <tbody>
                                                <tr>
                                                  <td style="height: 20px; width:20px; padding: 0px;
                                                    vertical-align: top;"><br>
                                                  </td>
                                                  <td style="height: 150px;" height="150">
                                                    <p style="margin-bottom: 5px; margin-top:0px;
                                                      text-align: center;"><img style="width: 70px;"
                                                        src="https://asgard.gifts/www/stopki/img/asgard_logo.png"></p>
                                                    <table style="width: 140px; display: block;">
                                                      <tbody>
                                                        <tr>
                                                          <td style="vertical-align: top;"><br>
                                                          </td>
                                                          <td><b style="font-size: 10px;
                                                              text-decoration: none; color: black;
                                                              line-height: 12px;">Asgard Sp. z o.o.<br>
                                                              ul. Rolna 17<br>
                                                              62-081 Baranowo<br>
                                                              <br>
                                                              pon.-pt. 8:00-16:00</b></td>
                                                        </tr>
                                                      </tbody>
                                                    </table>
                                                  </td>
                                                  <td style="height: 20px; width:20px; padding: 0px;
                                                    vertical-align: top;"> <br>
                                                  </td>
                                                </tr>
                                              </tbody>
                                            </table>
                                          </td>
                                          <td style="padding: 1px; background-color: #ff7300; height:
                                            145px;"> <br>
                                          </td>
                                          <td style="padding: 5px; height: 145px;"> <br>
                                          </td>
                                          <td style="height: 150px;">
                                            <table style="vertical-align: top; border-collapse:
                                              collapse; border-spacing: 0px; background-color:
                                              #f2f2f2; height: 150px;">
                                              <tbody>
                                                <tr>
                                                  <td style="height: 20px; width:20px; padding: 0px;
                                                    vertical-align: top;"><br>
                                                  </td>
                                                  <td style="text-align: center;">
                                                    <p style="margin-bottom: 5px;text-align: center;"><img
                                                        style="width: 130px; margin-top: 10px;"
                                                        src="https://asgard.gifts/www/stopki/img/bc_logo.png"
                                                        alt=""></p>
                                                    <table style="border-collapse: collapse;
                                                      border-spacing: 0px; margin-left: auto;
                                                      margin-right: auto; margin-top: 20px;
                                                      margin-bottom: 20px;">
                                                      <tbody>
                                                        <tr>
                                                          <td style="font-size: 10px;"> <b><a
                                                                style="color: black; text-decoration:
                                                                none;"
                                                                href="http://www.bluecollection.gifts">www.bluecollection.gifts</a></b>
                                                          </td>
                                                        </tr>
                                                      </tbody>
                                                    </table>
                                                    <p> <a
                                                        href="https://www.youtube.com/channel/UCrfLeqIN9LbTj6waa7P2NZw"><img
                                                          style="height: 27px;"
                                                          src="https://asgard.gifts/www/stopki/img/yt_black.png"
                                                          alt="YT -&gt; BLUE COLLECTION video"></a> <a
                                    href="https://www.instagram.com/bluecollection.gifts/"><img
                                                          style="height: 27px;"
                                                          src="https://asgard.gifts/www/stopki/img/instagram.png"
                                                          alt="Instagram -&gt; bluecollection.gifts"></a>
                                                    </p>
                                                  </td>
                                                  <td style="height: 20px; width:20px; padding: 0px;
                                                    vertical-align: top;"><br>
                                                  </td>
                                                </tr>
                                              </tbody>
                                            </table>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td colspan="7">
                                            <p style="color: #6b6b6b; font-size: 10px; text-align:
                                              center; margin-top: 10px;"> <b>KRS: </b>0000110082 <b>NIP: </b>781-17-05-028 <b>REGON: </b>634287574 <b>KONTO: </b>Santander Bank Polska S. A. 98 1910 1048 2263 0121 3834 0001<br>Sąd Rejonowy w Poznaniu VIII Wydział Gospodarczy Krajowego Rejestru Sądowego Kapitał Zakładowy 500 000,00 PLN opłacony w całości
                                              <br><b>BDO:</b>000006595  
                                              </p>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td colspan="7">
                                            <p style="color: #6b6b6b; font-size: 12px; text-align:
                                              center; margin-top: 10px;"> Zamówienia realizwane są zgodnie z OWW, dostępnymi <a href="https://asgard.gifts/warunki-wspolpracy.html">tutaj</a> Składając zamówienie, akceptujesz te warunki.
                                          </td>
                                        </tr>
                                        <br>
                                      </tbody>
                                    </table>
                                    <p style="text-align: center;">
                                    <span style="widows: 1; -webkit-text-stroke-width: 0px; float: none; word-spacing: 0px;">&nbsp;</span><br style="widows: 1; -webkit-text-stroke-width: 0px; word-spacing: 0px;">
                                    <span style="widows: 1; -webkit-text-stroke-width: 0px; float: none; word-spacing: 0px; font-size: 10px; color: #a5a5a5;">Jeśli nie chcesz dostawać takich wiadomości kliknij tutaj&nbsp; ##Link_Rezygnacji##</span><br>
                                    <br>
                                    <br>
                                    </p>
                                  </body>
                                </html>
                                """
            elif jezyk == 'EN':
                en_temat = dane_mailing['EN-temat']
                en_termin = dane_mailing['EN-termin']
                en_yt = dane_mailing['EN-yt']
                en_prezentacja = dane_mailing['EN-prezentacja']
                temat = en_temat
                content_mailingu = f"""
                                <html>
                                <head>                          
                                  <meta http-equiv="content-type" content="text/html; charset=UTF-8">
                                </head>
                                <body> 
                                <div style="padding: 100px;"> 
                                    <p>Dear customer,</p>
                                    <p>You probably remember, but let me remind you,<strong> that you are in a small group of our top customers.</strong> Therefore, I am again pleased to present you a pre-premiere of the new products that we are introducing each month as part of <strong>our Fantastic5 series.</strong> </p>
                                    <p>Here they are. </p>
                                    <p>Our latest Fantastic5 video presenting a set of products that won't be officially released until next week!</p>
                                    <p><strong>Watch it today by clicking on this link:</strong><a href="{en_yt}"> CLICK</a> </p>
                                    <p>You can view the product presentation in pdf file by clicking here:<a href="{en_prezentacja}"> CLICK</a> </p>
                                    <p>You can also view the previous Fantastic5 product series here:<a href="https://asgard.gifts/category/novelties-fantastic-5_262_1.html#"> CLICK</a> </p>
                                    <p>But that's not all!</p>
                                    <p><strong>I would like to invite you to a individual product presentation carried out by me exclusively for you.</strong> If you would like to attend, please let me know and we can arrange a convenient time for you.</p>
                                    <p>The products presented above will be added to our offer on<strong> {en_termin} of June.</strong> On that day they will appear in our online shop.</p>
                                    <p>On the day of its official premiere you will also receive from me an additional e-mail with the details of the new offer, an option to integrate it with your offer and materials that you can send to your clients.</p>
                                
                                
                                
                                <p style="font-size: 14px; margin-bottom: 10px;">Pozdrawiam serdecznie/ Cordialement/ Best Regards</p>
                                <table colspan="0" style="border-collapse: collapse;
                                  border-spacing: 0px; margin-top: 10px; color: black;" cellspacing="0" cellpadding="0">
                                  <tbody>
                                    <tr>
                                      <td style="height: 150px; ">
                                        <table style="vertical-align: top; border-collapse:
                                          collapse; border-spacing: 0px; background-color:
                                          #f2f2f2; height: 150px;" cellspacing="0" cellpadding="0">
                                          <tbody>
                                            <tr>
                                              <td style="height: 20px; width:20px; padding: 0px;
                                                vertical-align: top;"><br>
                                              </td>
                                              <td style="display: block; width: 140px;">
                                                <p style="margin-bottom: 5px; font-size: 15px;
                                                  margin-top: 20px;"><b>{imie}<br>{nazwisko}</b></p>
                                                <p style="font-size: 9px; margin-top: 5px;">EXPORT COORDINATOR</p>
                                                <table>
                                                  <tbody>
                                                    <tr>
                                                      <td style="font-size: 13px;"><b>{numer_tel}</b></td>
                                                    </tr>
                                                    <tr>
                                                      <td style="font-size: 11px;"><b><a style="color: black; text-decoration:
                                                            none;" href="http://www.asgard.gifts">www.asgard.gifts</a></b></td>
                                                    </tr>
                                                  </tbody>
                                                </table>
                                              </td>
                                              <td style="height: 20px; width:20px; padding: 0px;
                                                vertical-align: top;"> <br>
                                              </td>
                                            </tr>
                                          </tbody>
                                        </table>
                                      </td>
                                      <td style="padding: 1px; background-color: #ff7300; height:
                                        145px;"> <br>
                                      </td>
                                      <td style="padding: 5px; height: 145px;"> <br>
                                      </td>
                                      <td height="150px">
                                        <table style="vertical-align: top; border-collapse:
                                          collapse; border-spacing: 0px; background-color:
                                          #f2f2f2; height: 150px;" cellspacing="0" cellpadding="0" height="150">
                                          <tbody>
                                            <tr>
                                              <td style="height: 20px; width:20px; padding: 0px;
                                                vertical-align: top;"><br>
                                              </td>
                                              <td style="height: 150px;" height="150">
                                                <p style="margin-bottom: 5px; margin-top:0px;
                                                  text-align: center;"><img style="width: 70px;" src="https://asgard.gifts/www/stopki/img/asgard_logo.png"></p>
                                                <table style="width: 140px; display: block;">
                                                  <tbody>
                                                    <tr>
                                                      <td style="vertical-align: top;"><br>
                                                      </td>
                                                      <td><b style="font-size: 10px;
                                                          text-decoration: none; color: black;
                                                          line-height: 12px;">Asgard Sp. z o.o.<br>
                                                          ul. Rolna 17<br>
                                                          62-081 Baranowo<br>
                                                          <br>
                                                          pon.-pt. 8:00-16:00</b></td>
                                                    </tr>
                                                  </tbody>
                                                </table>
                                              </td>
                                              <td style="height: 20px; width:20px; padding: 0px;
                                                vertical-align: top;"> <br>
                                              </td>
                                            </tr>
                                          </tbody>
                                        </table>
                                      </td>
                                      <td style="padding: 1px; background-color: #ff7300; height:
                                        145px;"> <br>
                                      </td>
                                      <td style="padding: 5px; height: 145px;"> <br>
                                      </td>
                                      <td style="height: 150px;">
                                        <table style="vertical-align: top; border-collapse:
                                          collapse; border-spacing: 0px; background-color:
                                          #f2f2f2; height: 150px;">
                                          <tbody>
                                            <tr>
                                              <td style="height: 20px; width:20px; padding: 0px;
                                                vertical-align: top;"><br>
                                              </td>
                                              <td style="text-align: center;">
                                                <p style="margin-bottom: 5px;text-align: center;"><img style="width: 130px; margin-top: 10px;" src="https://asgard.gifts/www/stopki/img/bc_logo.png" alt=""></p>
                                                <table style="border-collapse: collapse;
                                                  border-spacing: 0px; margin-left: auto;
                                                  margin-right: auto; margin-top: 20px;
                                                  margin-bottom: 20px;">
                                                  <tbody>
                                                    <tr>
                                                      <td style="font-size: 10px;"> <b><a style="color: black; text-decoration:
                                                            none;" href="http://www.bluecollection.gifts">www.bluecollection.gifts</a></b>
                                                      </td>
                                                    </tr>
                                                  </tbody>
                                                </table>
                                                <p> <a href="https://www.youtube.com/channel/UCrfLeqIN9LbTj6waa7P2NZw"><img style="height: 27px;" src="https://asgard.gifts/www/stopki/img/yt_black.png" alt="YT -> BLUE COLLECTION video"></a> <a href="https://www.instagram.com/bluecollection.gifts/"><img style="height: 27px;" src="https://asgard.gifts/www/stopki/img/instagram.png" alt="Instagram -> bluecollection.gifts"></a>
                                                </p>
                                              </td>
                                              <td style="height: 20px; width:20px; padding: 0px;
                                                vertical-align: top;"><br>
                                              </td>
                                            </tr>
                                          </tbody>
                                        </table>
                                      </td>
                                    </tr>
                                    <tr>
                                      <td colspan="7">
                                        <p style="color: #6b6b6b; font-size: 10px; text-align:
                                          center; margin-top: 10px;"> <b>KRS: </b>0000110082 <b>NIP: </b>781-17-05-028 <b>REGON: </b>634287574 <b>KONTO: </b>Santander Bank Polska S. A. EUR PL44 1910 1048 2263 0121 3834 0003<br>Sąd Rejonowy w Poznaniu VIII Wydział Gospodarczy Krajowego Rejestru Sądowego Kapitał Zakładowy 500 000,00 PLN opłacony w całości 
                                          <br><b>BDO:</b>000006595</p>
                                      </td>
                                    </tr>
                                    <tr>
                                      
                                    </tr>
                                  </tbody>
                                </table>
                                </div>
                                <p style="text-align: center;">
                                    <span style="widows: 1; -webkit-text-stroke-width: 0px; float: none; word-spacing: 0px;">&nbsp;</span><br style="widows: 1; -webkit-text-stroke-width: 0px; word-spacing: 0px;">
                                    <span style="widows: 1; -webkit-text-stroke-width: 0px; float: none; word-spacing: 0px; font-size: 10px; color: #a5a5a5;">If you're not interested in receiving newsletters,
                                    click&nbsp; ##Link_Rezygnacji##</span><br>
                                    <br>
                                    <br>
                                    </p>
                                """
            elif jezyk == 'DE':
                de_temat = dane_mailing['DE-temat']
                de_termin = dane_mailing['DE-termin']
                de_yt = dane_mailing['DE-yt']
                de_prezentacja = dane_mailing['DE-prezentacja']
                temat = de_temat
                content_mailingu = f"""
                                    <html>
                                    <head>                          
                                      <meta http-equiv="content-type" content="text/html; charset=UTF-8">
                                    </head>
                                    <body> 
                                    <div style="padding: 100px;">
                                       <p>Sehr geehrter Kunde,</p>
                                        <p>Sie erinnern sich wahrscheinlich, aber ich  möchte Sie daran erinnern, <strong>dass Sie zu einer kleinen Gruppe unserer besten Kunden gehören.</strong> Deshalb freue ich mich, dass ich Ihnen vor der Premiere die neuen Produkte vorstellen kann, <strong>die wir jeden Monat im Rahmen  von Fantastik 5 in unser Offerte aufnehmen.</strong></p>
                                        <p>Hier ist es. </p>
                                        <p><strong>Unser neuestes Video aus Fantastic5</strong> zeigt eine Reihe von Produkten, deren offizielle Premiere in einer Woche stattfinden wird!</p>
                                        <p>Klicken Sie auf diesen Link, um es noch heute zu sehen: <a href="{de_yt}"> CLICK </a> </p>
                                        <p>Eine PDF-Präsentation der Produkte finden Sie unter folgendem Link: <a href="{de_prezentacja}"> CLICK </a> </p>
                                        <p>Die vorherige Serie von Fantastic5-Produkten kann hier angesehen werden: <a href="https://asgard.gifts/category/neue-fantastic-5_262_1.html#"> CLICK </a></p>
                                        <p>Aber es ist nicht alles!</p>
                                        <p><strong>Ich lade Sie zu einer individuellen Produktpräsentation ein, die ich exklusiv für Sie durchführe.</strong> Wenn Sie möchten, lassen Sie es mich wissen und wir werden einen für Sie passenden Termin vereinbaren.</p>
                                        <p>Die oben vorgestellten Produkte werden unserem Angebot am {de_termin} hinzugefügt. An diesem Tag erscheinen sie in unserem Online-Shop.</p>
                                        <p>Am Tag der offiziellen Premiere erhalten Sie von mir eine zusätzliche E-Mail mit den Details des neuen Angebots, der Möglichkeit, es in Ihr Angebot aufzunehmen, und Materialien, die Sie an Ihre Kunden senden können.</p>
                                    
                                     <br><table cellspacing="0" cellpadding="0" align="center">
                                    <tbody>
                                    <tr>
                                    <td style="display:none !important;
                                               visibility:hidden;
                                               mso-hide:all;
                                               font-size:1px;
                                               color:#ffffff;
                                               line-height:1px;
                                               max-height:0px;
                                               width:0px;
                                               opacity:0;
                                               overflow:hidden;">
                                    &lt;&lt; 📢 Wyjątkowa okazja, dla wyjątkowego klienta - zobacz nasze kwietniowe nowości z serii Fantastic5 na tydzień przed innymi!   &gt;&gt;
                                    </td>
                                    </tr>
                                    
                                    </tbody></table>
                                    <br>
                                    
                                    <p style="font-size: 14px; margin-bottom: 10px;">Pozdrawiam serdecznie/Mit freundlichen Grüßen/ Přeji přijemný den /Best Regards</p>
                                    <table colspan="0" style="border-collapse: collapse;
                                      border-spacing: 0px; margin-top: 10px; color: black;" cellspacing="0" cellpadding="0">
                                      <tbody>
                                        <tr>
                                          <td style="height: 150px; ">
                                            <table style="vertical-align: top; border-collapse:
                                              collapse; border-spacing: 0px; background-color:
                                              #f2f2f2; height: 150px;" cellspacing="0" cellpadding="0">
                                              <tbody>
                                                <tr>
                                                  <td style="height: 20px; width:20px; padding: 0px;
                                                    vertical-align: top;"><br>
                                                  </td>
                                                  <td style="display: block; width: 140px;">
                                                    <p style="margin-bottom: 5px; font-size: 15px;
                                                      margin-top: 20px;"><b>{imie}<br>{nazwisko}</b></p>
                                                    <p style="font-size: 9px; margin-top: 5px;">EXPORT COORDINATOR</p>
                                                    <table>
                                                      <tbody>
                                                        <tr>
                                                          <td style="font-size: 13px;"><b>{numer_tel}</b></td>
                                                        </tr>
                                                        <tr>
                                                          <td style="font-size: 11px;"><b><a style="color: black; text-decoration:
                                                                none;" href="http://www.asgard.gifts">www.asgard.gifts</a></b></td>
                                                        </tr>
                                                      </tbody>
                                                    </table>
                                                  </td>
                                                  <td style="height: 20px; width:20px; padding: 0px;
                                                    vertical-align: top;"> <br>
                                                  </td>
                                                </tr>
                                              </tbody>
                                            </table>
                                          </td>
                                          <td style="padding: 1px; background-color: #ff7300; height:
                                            145px;"> <br>
                                          </td>
                                          <td style="padding: 5px; height: 145px;"> <br>
                                          </td>
                                          <td height="150px">
                                            <table style="vertical-align: top; border-collapse:
                                              collapse; border-spacing: 0px; background-color:
                                              #f2f2f2; height: 150px;" cellspacing="0" cellpadding="0" height="150">
                                              <tbody>
                                                <tr>
                                                  <td style="height: 20px; width:20px; padding: 0px;
                                                    vertical-align: top;"><br>
                                                  </td>
                                                  <td style="height: 150px;" height="150">
                                                    <p style="margin-bottom: 5px; margin-top:0px;
                                                      text-align: center;"><img style="width: 70px;" src="https://asgard.gifts/www/stopki/img/asgard_logo.png"></p>
                                                    <table style="width: 140px; display: block;">
                                                      <tbody>
                                                        <tr>
                                                          <td style="vertical-align: top;"><br>
                                                          </td>
                                                          <td><b style="font-size: 10px;
                                                              text-decoration: none; color: black;
                                                              line-height: 12px;">Asgard Sp. z o.o.<br>
                                                              ul. Rolna 17<br>
                                                              62-081 Baranowo<br>
                                                              <br>
                                                              pon.-pt. 8:00-16:00</b></td>
                                                        </tr>
                                                      </tbody>
                                                    </table>
                                                  </td>
                                                  <td style="height: 20px; width:20px; padding: 0px;
                                                    vertical-align: top;"> <br>
                                                  </td>
                                                </tr>
                                              </tbody>
                                            </table>
                                          </td>
                                          <td style="padding: 1px; background-color: #ff7300; height:
                                            145px;"> <br>
                                          </td>
                                          <td style="padding: 5px; height: 145px;"> <br>
                                          </td>
                                          <td style="height: 150px;">
                                            <table style="vertical-align: top; border-collapse:
                                              collapse; border-spacing: 0px; background-color:
                                              #f2f2f2; height: 150px;">
                                              <tbody>
                                                <tr>
                                                  <td style="height: 20px; width:20px; padding: 0px;
                                                    vertical-align: top;"><br>
                                                  </td>
                                                  <td style="text-align: center;">
                                                    <p style="margin-bottom: 5px;text-align: center;"><img style="width: 130px; margin-top: 10px;" src="https://asgard.gifts/www/stopki/img/bc_logo.png" alt=""></p>
                                                    <table style="border-collapse: collapse;
                                                      border-spacing: 0px; margin-left: auto;
                                                      margin-right: auto; margin-top: 20px;
                                                      margin-bottom: 20px;">
                                                      <tbody>
                                                        <tr>
                                                          <td style="font-size: 10px;"> <b><a style="color: black; text-decoration:
                                                                none;" href="http://www.bluecollection.gifts">www.bluecollection.gifts</a></b>
                                                          </td>
                                                        </tr>
                                                      </tbody>
                                                    </table>
                                                    <p> <a href="https://www.youtube.com/channel/UCrfLeqIN9LbTj6waa7P2NZw"><img style="height: 27px;" src="https://asgard.gifts/www/stopki/img/yt_black.png" alt="YT -> BLUE COLLECTION video"></a> <a href="https://www.instagram.com/bluecollection.gifts/"><img style="height: 27px;" src="https://asgard.gifts/www/stopki/img/instagram.png" alt="Instagram -> bluecollection.gifts"></a>
                                                    </p>
                                                  </td>
                                                  <td style="height: 20px; width:20px; padding: 0px;
                                                    vertical-align: top;"><br>
                                                  </td>
                                                </tr>
                                              </tbody>
                                            </table>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td colspan="7">
                                            <p style="color: #6b6b6b; font-size: 10px; text-align:
                                              center; margin-top: 10px;"> <b>KRS: </b>0000110082 <b>NIP: </b>781-17-05-028 <b>REGON: </b>634287574 <b>KONTO: </b>Santander Bank Polska S. A. EUR PL44 1910 1048 2263 0121 3834 0003<br>Sąd Rejonowy w Poznaniu VIII Wydział Gospodarczy Krajowego Rejestru Sądowego Kapitał Zakładowy 500 000,00 PLN opłacony w całości 
                                              <br><b>BDO:</b>000006595</p>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td colspan="7">
                                            <p style="color: #6b6b6b; font-size: 12px; text-align:
                                              center; margin-top: 10px;"> Bestellungen werden gemäß den AGB ausgeführt, die Sie <a href="https://asgard.gifts/warunki-wspolpracy.html">hier einsehen können.</a><br>Mit einer Bestellung akzeptieren Sie diese Bedingungen. 
                                          </p></td>
                                        </tr>
                                      </tbody>
                                    </table>
                                    </div>
                                    <p style="text-align: center;">
                                        <span style="widows: 1; -webkit-text-stroke-width: 0px; float: none; word-spacing: 0px;">&nbsp;</span><br style="widows: 1; -webkit-text-stroke-width: 0px; word-spacing: 0px;">
                                        <span style="widows: 1; -webkit-text-stroke-width: 0px; float: none; word-spacing: 0px; font-size: 10px; color: #a5a5a5;">If you're not interested in receiving newsletters,
                                        click&nbsp; ##Link_Rezygnacji##</span><br>
                                        <br>
                                        <br>
                                        </p>
                                        """
            elif jezyk == 'FR':
                fr_temat = dane_mailing['FR-temat']
                fr_termin = dane_mailing['FR-termin']
                fr_yt = dane_mailing['FR-yt']
                fr_prezentacja = dane_mailing['FR-prezentacja']
                temat = fr_temat
                content_mailingu = f"""
                                    <html>
                                    <head>                          
                                      <meta http-equiv="content-type" content="text/html; charset=UTF-8">
                                    </head>
                                    <body> 
                                    <div style="padding: 100px;">
                                    <div style="padding: 100px;">
                                        <p>Cher client,</p>
                                            <p>Je suis sûr que vous vous en souvenez, mais laissez-moi vous rappeler que vous faites partie d'un <strong>petit groupe de nos meilleurs clients.</strong></p>
                                            <p>Par conséquent, je suis heureux de vous présenter les nouveaux produits, que nous introduisons chaque mois dans notre offre dans le cadre de la série Fantastic5.</p>
                                            <p><strong>Vérifiez- les avant la première!</strong></p>
                                            <p>C'est ici. </p>
                                            <p>Notre dernière vidéo de la série Fantastic5 présentant un ensemble de produits dont la première officielle aura lieu dans une semaine!</p>
                                            <p><strong>Découvrez-le aujourd'hui en cliquant sur ce lien:</strong> <a href="{fr_yt}"> CLICK</a> </p>
                                            <p>Vous pouvez consulter la présentation de produits sous forme de pdf en cliquant ici: <a href="{fr_prezentacja}"> CLICK</a> </p>
                                            <p>Vous pouvez voir la série précédente de produits de la série Fantastic5 ici: <a href="https://asgard.gifts/category/nouvelles-fantastic-5-_262_1.html#"> CLICK</a> </p>
                                            <p>Mais ce n'est pas tout!</p>
                                            <p><strong>Je vous invite à une présentation de produit individuelle réalisée par moi exclusivement pour vous.</strong> Si vous le souhaitez, faites-le moi savoir et nous organiserons une date convenable pour vous.</p>
                                            <p>Les produits présentés ci-dessus seront ajoutés à notre offre le {fr_termin} juin. Ce jour-là, ils apparaîtront dans notre boutique en ligne.</p>
                                            <p>Le jour de leur première officielle, vous recevrez également un e-mail supplémentaire de ma part avec les détails de la nouvelle offre, l'option d'intégration avec votre offre et les matériaux que vous pouvez envoyer à vos clients.</p>
                                        
                                        <p style="font-size: 14px; margin-bottom: 10px;">Pozdrawiam serdecznie/ Cordialement/ Best Regards</p>
                                        <table colspan="0" style="border-collapse: collapse;
                                          border-spacing: 0px; margin-top: 10px; color: black;" cellspacing="0" cellpadding="0">
                                          <tbody>
                                            <tr>
                                              <td style="height: 150px; ">
                                                <table style="vertical-align: top; border-collapse:
                                                  collapse; border-spacing: 0px; background-color:
                                                  #f2f2f2; height: 150px;" cellspacing="0" cellpadding="0">
                                                  <tbody>
                                                    <tr>
                                                      <td style="height: 20px; width:20px; padding: 0px;
                                                        vertical-align: top;"><br>
                                                      </td>
                                                      <td style="display: block; width: 140px;">
                                                        <p style="margin-bottom: 5px; font-size: 15px;
                                                          margin-top: 20px;"><b>{imie}<br>{nazwisko}</b></p>
                                                        <p style="font-size: 9px; margin-top: 5px;">EXPORT COORDINATOR</p>
                                                        <table>
                                                          <tbody>
                                                            <tr>
                                                              <td style="font-size: 13px;"><b>{numer_tel}</b></td>
                                                            </tr>
                                                            <tr>
                                                              <td style="font-size: 11px;"><b><a style="color: black; text-decoration:
                                                                    none;" href="http://www.asgard.gifts">www.asgard.gifts</a></b></td>
                                                            </tr>
                                                          </tbody>
                                                        </table>
                                                      </td>
                                                      <td style="height: 20px; width:20px; padding: 0px;
                                                        vertical-align: top;"> <br>
                                                      </td>
                                                    </tr>
                                                  </tbody>
                                                </table>
                                              </td>
                                              <td style="padding: 1px; background-color: #ff7300; height:
                                                145px;"> <br>
                                              </td>
                                              <td style="padding: 5px; height: 145px;"> <br>
                                              </td>
                                              <td height="150px">
                                                <table style="vertical-align: top; border-collapse:
                                                  collapse; border-spacing: 0px; background-color:
                                                  #f2f2f2; height: 150px;" cellspacing="0" cellpadding="0" height="150">
                                                  <tbody>
                                                    <tr>
                                                      <td style="height: 20px; width:20px; padding: 0px;
                                                        vertical-align: top;"><br>
                                                      </td>
                                                      <td style="height: 150px;" height="150">
                                                        <p style="margin-bottom: 5px; margin-top:0px;
                                                          text-align: center;"><img style="width: 70px;" src="https://asgard.gifts/www/stopki/img/asgard_logo.png"></p>
                                                        <table style="width: 140px; display: block;">
                                                          <tbody>
                                                            <tr>
                                                              <td style="vertical-align: top;"><br>
                                                              </td>
                                                              <td><b style="font-size: 10px;
                                                                  text-decoration: none; color: black;
                                                                  line-height: 12px;">Asgard Sp. z o.o.<br>
                                                                  ul. Rolna 17<br>
                                                                  62-081 Baranowo<br>
                                                                  <br>
                                                                  pon.-pt. 8:00-16:00</b></td>
                                                            </tr>
                                                          </tbody>
                                                        </table>
                                                      </td>
                                                      <td style="height: 20px; width:20px; padding: 0px;
                                                        vertical-align: top;"> <br>
                                                      </td>
                                                    </tr>
                                                  </tbody>
                                                </table>
                                              </td>
                                              <td style="padding: 1px; background-color: #ff7300; height:
                                                145px;"> <br>
                                              </td>
                                              <td style="padding: 5px; height: 145px;"> <br>
                                              </td>
                                              <td style="height: 150px;">
                                                <table style="vertical-align: top; border-collapse:
                                                  collapse; border-spacing: 0px; background-color:
                                                  #f2f2f2; height: 150px;">
                                                  <tbody>
                                                    <tr>
                                                      <td style="height: 20px; width:20px; padding: 0px;
                                                        vertical-align: top;"><br>
                                                      </td>
                                                      <td style="text-align: center;">
                                                        <p style="margin-bottom: 5px;text-align: center;"><img style="width: 130px; margin-top: 10px;" src="https://asgard.gifts/www/stopki/img/bc_logo.png" alt=""></p>
                                                        <table style="border-collapse: collapse;
                                                          border-spacing: 0px; margin-left: auto;
                                                          margin-right: auto; margin-top: 20px;
                                                          margin-bottom: 20px;">
                                                          <tbody>
                                                            <tr>
                                                              <td style="font-size: 10px;"> <b><a style="color: black; text-decoration:
                                                                    none;" href="http://www.bluecollection.gifts">www.bluecollection.gifts</a></b>
                                                              </td>
                                                            </tr>
                                                          </tbody>
                                                        </table>
                                                        <p> <a href="https://www.youtube.com/channel/UCrfLeqIN9LbTj6waa7P2NZw"><img style="height: 27px;" src="https://asgard.gifts/www/stopki/img/yt_black.png" alt="YT -> BLUE COLLECTION video"></a> <a href="https://www.instagram.com/bluecollection.gifts/"><img style="height: 27px;" src="https://asgard.gifts/www/stopki/img/instagram.png" alt="Instagram -> bluecollection.gifts"></a>
                                                        </p>
                                                      </td>
                                                      <td style="height: 20px; width:20px; padding: 0px;
                                                        vertical-align: top;"><br>
                                                      </td>
                                                    </tr>
                                                  </tbody>
                                                </table>
                                              </td>
                                            </tr>
                                            <tr>
                                              <td colspan="7">
                                                <p style="color: #6b6b6b; font-size: 10px; text-align:
                                                  center; margin-top: 10px;"> <b>KRS: </b>0000110082 <b>NIP: </b>781-17-05-028 <b>REGON: </b>634287574 <b>KONTO: </b>Santander Bank Polska S. A. EUR PL44 1910 1048 2263 0121 3834 0003<br>Sąd Rejonowy w Poznaniu VIII Wydział Gospodarczy Krajowego Rejestru Sądowego Kapitał Zakładowy 500 000,00 PLN opłacony w całości 
                                                  <br><b>BDO:</b>000006595</p>
                                              </td>
                                            </tr>
                                            <tr>
                                              <td colspan="7">
                                                <p style="color: #6b6b6b; font-size: 12px; text-align:
                                                  center; margin-top: 10px;">  Les commandes sont effectuées conformément aux CGV, disponibles <a href="https://asgard.gifts/warunki-wspolpracy.html">ici.</a> En passant une commande, vous acceptez ces conditions.
                                              </p></td>
                                            </tr>
                                          </tbody>
                                        </table>
                                        </div>
                                        <p style="text-align: center;">
                                            <span style="widows: 1; -webkit-text-stroke-width: 0px; float: none; word-spacing: 0px;">&nbsp;</span><br style="widows: 1; -webkit-text-stroke-width: 0px; word-spacing: 0px;">
                                            <span style="widows: 1; -webkit-text-stroke-width: 0px; float: none; word-spacing: 0px; font-size: 10px; color: #a5a5a5;">If you're not interested in receiving newsletters,
                                            click&nbsp; ##Link_Rezygnacji##</span><br>
                                            <br>
                                            <br>
                                            </p>
                                    """

            for itemRedlink in lista_grup_redlink_handlowcy:
                if itemRedlink['GroupName'].endswith(f'{jezyk}') and itemRedlink['GroupName'].startswith('VIP'):
                    nazwa_grupy = itemRedlink['GroupName'].replace('VIP_', '')
                    nazwisko_grypa_redlink = re.findall(r'([A-Z][a-z]*$)', nazwa_grupy.split('_')[0])[0]
                    if nazwisko == nazwisko_grypa_redlink:
                        grup_id= itemRedlink['GroupId']

            #id_kampanii = wyslij_VIP_redlink(nazwa_mailingu, temat, imie_nazwisko_handlowca, mail_wysylki, content_mailingu,
            #                   data_wyslania, grup_id)
            Handlowiec.objects.create(redlink_id= id_kampanii, jezyk=jezyk.lower(), ctr=0, open_rate=0,
                                      dostarczone_wiadomosci=0, un_sub=0,
                                      imie_nazwisko=imie_nazwisko_handlowca)
    return redirect('http://127.0.0.1:8000/')


def unsubscribe(request):
    return render(request, 'unsubscribe.html')

def stats_unsubscribe(request):
    return render(request, 'stats_unsubscribe.html')