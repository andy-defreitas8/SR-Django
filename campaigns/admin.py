from django.contrib import admin
from django import forms
from .models import Client, Campaign, Product_Mapping, Page_Mapping, Commercial, ga_product, ga_page
from .forms import PageMappingForm, ProductMappingForm


@admin.register(Client)
class ClientsAdmin(admin.ModelAdmin):
    list_display = ['name', 'client_id', 'daily_activity_start_time', 'daily_activity_end_time', 'attribution_window_duration', 'ga4_filename', 'start_date']
    list_filter = ['start_date']
    search_fields = ['name']
    readonly_fields = ['client_id']

    # def get_readonly_fields(self, request, obj = None):
    #     if obj:
    #         return['client_id']
    #     return []

@admin.register(Campaign)
class CampaignsAdmin(admin.ModelAdmin):
    list_display = [ 'name', 'campaign_id', 'client_id']
    search_fields = ['name']
    readonly_fields = ['campaign_id']

    # def get_readonly_fields(self, request, obj = None):
    #     if obj:
    #         return['campaign_id']
    #     return []

@admin.register(Product_Mapping)
class ProductMappingAdmin(admin.ModelAdmin):
    form = ProductMappingForm
    list_display = ['ga_product', 'campaign', 'map_id']
    
    # def get_fields(self, request, obj = None):
    #     return ['ga_product', 'campaign']
    
@admin.register(Page_Mapping)
class Page_MappingAdmin(admin.ModelAdmin):
    form = PageMappingForm
    list_display = ['ga_page', 'campaign', 'map_id']

    # def get_fields(self, request, obj = None):
    #     return ['ga_page', 'campaign']
    
@admin.register(Commercial)
class CommercialAdmin(admin.ModelAdmin):
    list_display = ['clearcast_commercial_title', 'commercial_id', 'advertiser_id', 'campaign_id', 'commercial_number', 'web_address']
    readonly_fields = ['commercial_id', 'advertiser_id', 'clearcast_commercial_title', 'commercial_number', 'web_address']
    search_fields = ['clearcast_commercial_title']

    def has_add_permission(self, request):
        return False
    
    def get_readonly_fields(self, request, obj = ...):
        if obj:
            return['commercial_id', 'advertiser_id', 'clearcast_commercial_title', 'commercial_number', 'web_address']
        return self.fields
    
    def has_delete_permission(self, request, obj = ...):
        return False
    
