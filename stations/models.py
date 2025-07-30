from django.db import models

class Pricing_Sheet(models.Model):
    price_date = models.DateField(primary_key=True)
    note = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'sr_pricing_sheets'

    def __str__(self):
        return f"Pricing Sheet for {self.price_date}"

class Station(models.Model):
    station_id = models.BigAutoField(primary_key=True)
    station_name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'sr_stations'

class Station_pricing(models.Model):
    station_pricing_id = models.BigAutoField(primary_key=True)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    price_date = models.ForeignKey(Pricing_Sheet, on_delete=models.CASCADE, db_column='price_date')
    cost_type = models.CharField(max_length=100)
    cost = models.FloatField()

    class Meta:
        managed = False
        db_table = 'sr_station_pricings'

    def __str__(self):
        return f"Pricing Sheet for {self.price_date}"