from django.db import models

# Create your models here.


class KampaniaRedlink(models.Model):
    nazwa_kampanii = models.CharField(max_length=100)
    kiedy_wyslany = models.CharField(max_length=100)
    temat_mailingu_pl = models.CharField(max_length=100)
    temat_mailingu_en = models.CharField(max_length=100)
    temat_mailingu_de = models.CharField(max_length=100)
    temat_mailingu_fr = models.CharField(max_length=100)
    link_content = models.CharField(max_length=200)
    ctr_pl = models.FloatField(default=0)
    open_rate_pl = models.FloatField(default=0)
    ctr_en = models.FloatField(default=0)
    open_rate_en = models.FloatField(default=0)
    ctr_de = models.FloatField(default=0)
    open_rate_de = models.FloatField(default=0)
    ctr_fr = models.FloatField(default=0)
    open_rate_fr = models.FloatField(default=0)
    dostarczone_wiadomosci_pl = models.IntegerField(default=0)
    dostarczone_wiadomosci_en = models.IntegerField(default=0)
    dostarczone_wiadomosci_de = models.IntegerField(default=0)
    dostarczone_wiadomosci_fr = models.IntegerField(default=0)
    un_sub_pl = models.IntegerField(default=0)
    un_sub_en = models.IntegerField(default=0)
    un_sub_de = models.IntegerField(default=0)
    un_sub_fr = models.IntegerField(default=0)
    hard_bounces_pl = models.IntegerField(default=0)
    hard_bounces_en = models.IntegerField(default=0)
    hard_bounces_de = models.IntegerField(default=0)
    hard_bounces_fr = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.nazwa_kampanii} -- {self.kiedy_wyslany}'


class Handlowiec (models.Model):
    redlink_id = models.CharField(max_length=100)
    jezyk = models.CharField(max_length=100)
    ctr = models.FloatField(default=0)
    open_rate = models.FloatField(default=0)
    dostarczone_wiadomosci = models.IntegerField(default=0)
    un_sub = models.IntegerField(default=0)
    nazwa_kampanii = models.CharField(max_length=100, default='test')
    imie_nazwisko = models.CharField(max_length=100, default='test')
    hard_bounces = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.nazwa_kampanii} -- {self.imie_nazwisko} -- {self.jezyk}'
