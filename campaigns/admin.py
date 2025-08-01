from django.contrib import admin
from django import forms
from .models import Client, Campaign, Product_Mapping, Page_Mapping, Commercial, ga_product, ga_page
from .forms import CommercialInlineForm

admin.site.site_header = "Smart Response Campaign Management Portal"
admin.site.site_title = "Campaign Portal Admin"
admin.site.index_title = "Welcome to the Campaign Admin"

class ProductMappingInline(admin.TabularInline):
    model = Product_Mapping
    extra = 1
    fields = ['ga_product']


class PageMappingInline(admin.TabularInline):
    model = Page_Mapping
    extra = 1
    fields = ['ga_page']


class CommercialInline(admin.TabularInline):
    model = Commercial
    extra = 1
    fields = ['commercial']
    form = CommercialInlineForm
    can_delete = False


@admin.register(Client)
class ClientsAdmin(admin.ModelAdmin):
    list_display = ['name', 'daily_activity_start_time', 'daily_activity_end_time', 'attribution_window_duration', 'ga4_filename', 'start_date']
    list_filter = ['start_date']
    search_fields = ['name']


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'client']
    search_fields = ['name']
    inlines = [ProductMappingInline, PageMappingInline, CommercialInline]

    def get_fields(self, request, obj=None):
        return ['client', 'name']


@admin.register(Product_Mapping)
class ProductMappingAdmin(admin.ModelAdmin):
    list_display = ['ga_product', 'campaign']
    
    
@admin.register(Page_Mapping)
class Page_MappingAdmin(admin.ModelAdmin):
    list_display = ['ga_page', 'campaign']

    
@admin.register(Commercial)
class CommercialAdmin(admin.ModelAdmin):
    list_display = ['clearcast_commercial_title', 'commercial_id', 'advertiser_id', 'campaign_id', 'commercial_number', 'web_address']
    search_fields = ['clearcast_commercial_title']

    def has_add_permission(self, request):
        return False
    
    def get_readonly_fields(self, request, obj = ...):
        if obj:
            return['commercial_id', 'advertiser_id', 'clearcast_commercial_title', 'commercial_number', 'web_address']
        return self.fields
    
    def has_delete_permission(self, request, obj = ...):
        return False

    
