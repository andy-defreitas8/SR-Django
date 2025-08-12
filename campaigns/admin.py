from django.contrib import admin
from django import forms
from .models import Client, Campaign, Product_Mapping, Page_Mapping, Commercial, Product, Page
from .forms import CommercialInlineForm

admin.site.site_header = "Smart Response Campaign Management Portal"
admin.site.site_title = "Campaign Portal Admin"
admin.site.index_title = "Welcome to the Campaign Admin"

class ProductMappingInline(admin.TabularInline):
    model = Product_Mapping
    extra = 1
    fields = ['ga_product']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'ga_product':
            client_id = request.GET.get('client_id')
            if client_id:
                kwargs["queryset"] = Product.objects.filter(client_id=client_id)
            else:
                kwargs["queryset"] = Product.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class PageMappingInline(admin.TabularInline):
    model = Page_Mapping
    extra = 1
    fields = ['ga_page']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'ga_page':
            client_id = request.GET.get('client_id')
            if client_id:
                kwargs["queryset"] = Page.objects.filter(client_id=client_id)
            else:
                kwargs["queryset"] = Page.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


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
    
    def get_changeform_initial_data(self, request):
        # Pull client_id from the URL query and prefill the field
        client_id = request.GET.get('client_id')
        initial = super().get_changeform_initial_data(request)
        if client_id:
            initial['client'] = client_id
        return initial
    
    class Media:
        js = ('campaigns/js/client_filtering.js',)


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


