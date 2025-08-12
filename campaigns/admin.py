from django.contrib import admin, messages
from django import forms
from .models import Client, Campaign, Product_Mapping, Page_Mapping, Commercial, Product, Page
from django.shortcuts import render, redirect
from django.urls import path

admin.site.site_header = "Smart Response Campaign Management Portal"
admin.site.site_title = "Campaign Portal Admin"
admin.site.index_title = "Welcome to the Campaign Admin"

# Form for selecting a campaign
from django import forms
class CampaignSelectForm(forms.Form):
    campaign = forms.ModelChoiceField(queryset=Campaign.objects.all(), required=True)


class CampaignInline(admin.TabularInline):
    model = Campaign
    extra = 1  # always show 1 empty form for adding a campaign
    fields = ['name']
    show_change_link = True  # link to edit the campaign in full form
    can_delete = True        # allow deletion from client page

class ProductMappingInline(admin.TabularInline):
    model = Product_Mapping
    extra = 0
    can_delete = False
    readonly_fields = ['product_name']
    fields = ['product_name']
    show_change_link = False

    def product_name(self, obj):
        return obj.ga_product.item_name if obj.ga_product else "-"
    product_name.short_description = "Product"

    def has_add_permission(self, request, obj):
        return False


class PageMappingInline(admin.TabularInline):
    model = Page_Mapping
    extra = 0
    can_delete = False
    readonly_fields = ['page_url']
    fields = ['page_url']
    show_change_link = False

    def page_url(self, obj):
        return obj.ga_page.url if obj.ga_page else "-"
    page_url.short_description = "Page"

    def has_add_permission(self, request, obj):
        return False


class CommercialInline(admin.TabularInline):
    model = Commercial
    extra = 0
    can_delete = False
    readonly_fields = ['commercial_title']
    fields = ['commercial_title']
    show_change_link = False

    def commercial_title(self, obj):
        return obj.clearcast_commercial_title if obj.clearcast_commercial_title else "-"
    commercial_title.short_description = "Commercial"

    def has_add_permission(self, request, obj):
        return False


@admin.register(Client)
class ClientsAdmin(admin.ModelAdmin):
    list_display = ['name', 'daily_activity_start_time', 'daily_activity_end_time', 'attribution_window_duration', 'ga4_filename', 'start_date']
    list_filter = ['start_date']
    search_fields = ['name']
    inlines = [CampaignInline]


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
        # css = {
        #     'all': ('admin/css/custom_admin.css',)
        # }

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'client')
    search_fields = ['item_name']
    actions = ['map_to_campaign_action']
    list_filter = ['client']

    def map_to_campaign_action(self, request, queryset):
        # Store IDs of selected products in session
        request.session['selected_product_ids'] = list(queryset.values_list('pk', flat=True))
        return redirect('admin:product_map_to_campaign')

    map_to_campaign_action.short_description = "Map to campaign"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('map-to-campaign/', self.admin_site.admin_view(self.map_to_campaign_view), name='product_map_to_campaign'),
        ]
        return custom_urls + urls

    def map_to_campaign_view(self, request):
        selected_ids = request.session.get('selected_product_ids', [])
        if not selected_ids:
            self.message_user(request, "No products selected.", level=messages.WARNING)
            return redirect('..')

        if request.method == "POST":
            form = CampaignSelectForm(request.POST)
            if form.is_valid():
                campaign = form.cleaned_data['campaign']
                # Create mappings
                for pid in selected_ids:
                    Product_Mapping.objects.get_or_create(
                        ga_product_id=pid,
                        campaign=campaign
                    )
                self.message_user(request, f"Mapped {len(selected_ids)} products to '{campaign.name}'.", level=messages.SUCCESS)
                request.session.pop('selected_product_ids', None)
                return redirect('..')
        else:
            form = CampaignSelectForm()

        context = dict(
            self.admin_site.each_context(request),
            title="Map Products to Campaign",
            form=form,
            selected_count=len(selected_ids),
        )
        return render(request, "admin/map_to_campaign.html", context)


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('url', 'client')
    search_fields = ['url']
    actions = ['map_to_campaign_action']
    list_filter = ['client']

    def map_to_campaign_action(self, request, queryset):
        request.session['selected_page_ids'] = list(queryset.values_list('pk', flat=True))
        return redirect('admin:page_map_to_campaign')

    map_to_campaign_action.short_description = "Map to campaign"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('map-to-campaign/', self.admin_site.admin_view(self.map_to_campaign_view), name='page_map_to_campaign'),
        ]
        return custom_urls + urls

    def map_to_campaign_view(self, request):
        selected_ids = request.session.get('selected_page_ids', [])
        if not selected_ids:
            self.message_user(request, "No pages selected.", level=messages.WARNING)
            return redirect('..')

        if request.method == "POST":
            form = CampaignSelectForm(request.POST)
            if form.is_valid():
                campaign = form.cleaned_data['campaign']
                for pid in selected_ids:
                    Page_Mapping.objects.get_or_create(
                        ga_page_id=pid,
                        campaign=campaign
                    )
                self.message_user(request, f"Mapped {len(selected_ids)} pages to '{campaign.name}'.", level=messages.SUCCESS)
                request.session.pop('selected_page_ids', None)
                return redirect('..')
        else:
            form = CampaignSelectForm()

        context = dict(
            self.admin_site.each_context(request),
            title="Map Pages to Campaign",
            form=form,
            selected_count=len(selected_ids),
        )
        return render(request, "admin/map_to_campaign.html", context)

    
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


