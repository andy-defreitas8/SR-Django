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

class Campaign(models.Model):
    campaign_id = models.BigAutoField(primary_key=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    name= models.CharField(max_length=100)

    class Meta:
        managed=False
        db_table = 'sr_campaigns'
    
    def __str__(self):
        return self.name

class ga_product(models.Model):
    client_id = models.BigIntegerField()
    ga_product_id = models.BigIntegerField(primary_key=True)
    item_id = models.TextField()
    item_name = models.TextField()

    class Meta:
        managed = False
        db_table = 'ga_products'

    def __str__(self):
        return self.item_name

class ga_page(models.Model):
    client_id = models.BigIntegerField()
    ga_page_id = models.BigIntegerField(primary_key=True)
    url = models.TextField()

    class Meta:
        managed = False
        db_table = 'ga_pages'

class Product_Mapping(models.Model):
    ga_product = models.ForeignKey(ga_product, on_delete=models.CASCADE)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    map_id = models.BigAutoField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'sr_product_mappings'

class Page_Mapping(models.Model):
    ga_page = models.ForeignKey(ga_page, on_delete=models.CASCADE)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    map_id = models.BigAutoField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'sr_page_mappings'

class Commercial(models.Model):
    commercial_id = models.BigAutoField(primary_key=True)
    advertiser_id = models.BigIntegerField()
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    clearcast_commercial_title = models.CharField()
    commercial_number = models.CharField()
    web_address = models.CharField()

    class Meta:
        managed = False
        db_table = 'sr_commercials'

    def __str__(self):
        return self.clearcast_commercial_title or f"Commercial {self.commercial_id}"