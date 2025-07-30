from django.contrib import admin
from .models import Pricing_Sheet, Station_pricing, Station

@admin.register(Pricing_Sheet)
class PricingSheetAdmin(admin.ModelAdmin):
    list_display = ['price_date', 'note']
    list_filter = ['price_date']
    search_fields = ['price_date']

@admin.register(Station_pricing)
class StationPricingAdmin(admin.ModelAdmin):
    list_display = ['station_id', 'price_date', 'cost_type', 'cost']
    list_filter = ['price_date']
    autocomplete_fields = ['price_date']
