from django.contrib import admin
from django import forms
from .models import Client, Campaign, Product_Mapping, Page_Mapping, Commercial, ga_product, ga_page
from .forms import CampaignForm, PageMappingForm, ProductMappingForm

admin.site.site_header = "Smart Response Campaign Management Portal"
admin.site.site_title = "Campaign Portal Admin"
admin.site.index_title = "Welcome to the Campaign Admin"

@admin.register(Client)
class ClientsAdmin(admin.ModelAdmin):
    list_display = ['name', 'daily_activity_start_time', 'daily_activity_end_time', 'attribution_window_duration', 'ga4_filename', 'start_date']
    list_filter = ['start_date']
    search_fields = ['name']

    # def get_readonly_fields(self, request, obj = None):
    #     if obj:
    #         return['client_id']
    #     return []

@admin.register(Campaign)
class CampaignsAdmin(admin.ModelAdmin):
    list_display = [ 'name', 'client']
    search_fields = ['name']
    form = CampaignForm

    def get_fields(self, request, obj=None):
        return ['client', 'name', 'product', 'page', 'commercial']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        product = form.cleaned_data.get('product')
        page = form.cleaned_data.get('page')
        commercial = form.cleaned_data.get('commercial')

        if product:
            Product_Mapping.objects.create(
                campaign=obj,
                ga_product=product
            )

        if page:
            Page_Mapping.objects.create(
                campaign=obj,
                ga_page=page
            )

        if commercial:
            commercial.campaign = obj
            commercial.save(update_fields=['campaign'])



@admin.register(Product_Mapping)
class ProductMappingAdmin(admin.ModelAdmin):
    form = ProductMappingForm
    list_display = ['ga_product', 'campaign']
    
    # def get_fields(self, request, obj = None):
    #     return ['ga_product', 'campaign']
    
@admin.register(Page_Mapping)
class Page_MappingAdmin(admin.ModelAdmin):
    form = PageMappingForm
    list_display = ['ga_page', 'campaign']

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
    
