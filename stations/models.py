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

    def __str__(self):
        return self.station_name

class Hour(models.Model):
    hour = models.IntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'hours'

    def __str__(self):
        return str(self.hour)

class Duration(models.Model):
    duration_seconds = models.IntegerField(primary_key=True)

    class Meta:
        managed = False 
        db_table = 'spot_duration'

    def __str__(self):
        return str(self.duration_seconds)

class Sales_House(models.Model):
    sales_house_id = models.BigAutoField(primary_key=True)
    sales_house_name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'sr_sales_houses'

    def __str__(self):
        return self.sales_house_name

class Station_pricing(models.Model):
    price_id = models.BigAutoField(primary_key=True)
    price_date = models.ForeignKey(Pricing_Sheet, on_delete=models.CASCADE, db_column='price_date')
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    start_hour = models.ForeignKey(Hour, on_delete=models.CASCADE, db_column = 'start_hour', related_name='start_hour', name='start_hour')
    end_hour = models.ForeignKey(Hour, on_delete=models.CASCADE, db_column = 'end_hour', related_name='end_hour', name='end_hour')
    duration = models.ForeignKey(Duration, on_delete=models.CASCADE, db_column='duration')
    sales_house = models.ForeignKey(Sales_House, on_delete=models.CASCADE)
    cost_type = models.CharField(max_length=3)
    cost = models.FloatField()

    class Meta:
        managed = False
        db_table = 'sr_station_prices'

