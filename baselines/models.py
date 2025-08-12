from django.db import models

class Client(models.Model):
    client_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    daily_activity_start_time = models.TimeField()
    daily_activity_end_time = models.TimeField()
    attribution_window_duration = models.IntegerField()
    ga4_filename = models.CharField(max_length=200)
    start_date = models.DateField()

    class Meta:
        managed = False
        db_table = 'sr_clients'

    def __str__(self):
        return self.name

class Product(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    ga_product_id = models.BigIntegerField(primary_key=True)
    item_id = models.CharField(max_length=100)
    item_name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'ga_products' 

    def __str__(self):
        return self.item_name
    
class Page(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    ga_page_id = models.BigIntegerField(primary_key=True)
    url = models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = 'ga_pages'

    def __str__(self):
        return self.url

class Product_Baseline(models.Model):
    ga_product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='ga_product_id')
    day_of_week = models.CharField(max_length=3)
    hour_of_day = models.IntegerField()
    baseline_session = models.FloatField()
    baseline_sales = models.FloatField()

    class Meta:
        managed = False
        db_table = 'product_baselines'

class Page_Baseline(models.Model):
    ga_page_id = models.ForeignKey(Page, on_delete=models.CASCADE, db_column='ga_page_id')
    day_of_week = models.CharField(max_length=3)
    hour_of_day = models.IntegerField()
    baseline_session = models.FloatField()
    baseline_sales = models.FloatField()

    class Meta:
        managed = False
        db_table = 'page_baselines'


