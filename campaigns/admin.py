from django.contrib import admin, messages
from django import forms
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.http import HttpResponse
from django.db import connection
from django.utils.html import format_html
import csv
from io import TextIOWrapper
import pandas as pd

from .models import Client, Campaign, Product_Mapping, Page_Mapping, Commercial, Product, Page

admin.site.site_header = "Smart Response Campaign Management Portal"
admin.site.site_title = "Campaign Portal Admin"
admin.site.index_title = "Welcome to the Campaign Admin"

BASELINE_COLUMNS = ['day_of_week', 'hour_of_day', 'baseline_session', 'baseline_sales']

# Form for selecting a campaign
class CampaignSelectForm(forms.Form):
    campaign = forms.ModelChoiceField(queryset=Campaign.objects.all(), required=True)

class BaselineAdminMixin:
    """Shared baseline export/upload + mapping logic for products/pages."""

    export_view_name = None
    upload_view_name = None
    map_view_name = None
    baseline_table = None
    id_field = None
    mapping_model = None
    mapping_fk_name = None  # 'ga_product_id' or 'ga_page_id'

    list_filter = ('client',)
    actions = ['upload_baseline_csv_action', 'map_to_campaign_action']

    # ==== Export Button ====
    def export_link(self, obj):
        return format_html(
            '<a class="button" href="{}">Export Baseline CSV</a>',
            reverse(f'admin:{self.export_view_name}', args=[obj.pk])
        )
    export_link.short_description = "Export"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # Export baseline for single object
            path(
                '<path:object_id>/export-baseline/',
                self.admin_site.admin_view(self.export_baseline),
                name=self.export_view_name
            ),
            # Upload baseline for multiple
            path(
                'upload-baseline/',
                self.admin_site.admin_view(self.upload_csv_view),
                name=self.upload_view_name
            ),
            # Map to campaign
            path(
                'map-to-campaign/',
                self.admin_site.admin_view(self.map_to_campaign_view),
                name=self.map_view_name
            ),
        ]
        return custom_urls + urls

    # ==== Export ====
    def export_baseline(self, request, object_id):
        obj = self.model.objects.get(pk=object_id)
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT day_of_week, hour_of_day, baseline_session, baseline_sales
                FROM {self.baseline_table}
                WHERE {self.id_field} = %s
                ORDER BY day_of_week, hour_of_day
                """,
                [getattr(obj, self.id_field)]
            )
            rows = cursor.fetchall()

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{getattr(obj, self.id_field)}_baseline.csv"'
        writer = csv.writer(response)
        writer.writerow(BASELINE_COLUMNS)
        for row in rows:
            writer.writerow(row)
        return response

    # ==== Upload Baseline Action ====
    def upload_baseline_csv_action(self, request, queryset):
        ids = list(queryset.values_list(self.id_field, flat=True))
        request.session['upload_baseline_ids'] = ids
        return redirect(f'admin:{self.upload_view_name}')
    upload_baseline_csv_action.short_description = "Upload baseline csv"

    def upload_csv_view(self, request):
        selected_ids = request.session.get('upload_baseline_ids', [])
        if request.method == "POST":
            uploaded_file = request.FILES.get("csv_file")
            if not uploaded_file:
                self.message_user(request, "No file uploaded", level=messages.ERROR)
                return redirect(f'admin:{self.upload_view_name}')

            if not uploaded_file.name.lower().endswith('.csv'):
                self.message_user(request, "The uploaded file must be a .csv", level=messages.ERROR)
                return redirect(f'admin:{self.upload_view_name}')

            try:
                df = pd.read_csv(TextIOWrapper(uploaded_file.file, encoding='utf-8'))

                if not set(BASELINE_COLUMNS).issubset(df.columns):
                    missing = set(BASELINE_COLUMNS) - set(df.columns)
                    self.message_user(request, f"Missing required columns: {', '.join(missing)}", level=messages.ERROR)
                    return redirect(f'admin:{self.upload_view_name}')

                missing_required = df[BASELINE_COLUMNS].isnull().any()
                if missing_required.any():
                    missing_cols = missing_required[missing_required == True].index.tolist()
                    self.message_user(request, f"Missing required values in: {', '.join(missing_cols)}", level=messages.ERROR)
                    return redirect(f'admin:{self.upload_view_name}')

                cleaned_data = df[BASELINE_COLUMNS].to_dict(orient='records')
                request.session['validated_baseline_data'] = cleaned_data
                self.message_user(
                    request,
                    f"Validated {len(cleaned_data)} rows for {len(selected_ids)} selected items. Ready to insert.",
                    level=messages.SUCCESS
                )
                return redirect('../')
            except Exception as e:
                self.message_user(request, f"Error processing CSV: {e}", level=messages.ERROR)
                return redirect(f'admin:{self.upload_view_name}')

        return render(request, "admin/upload_baseline_csv.html", {
            "count": len(selected_ids),
            "columns": BASELINE_COLUMNS
        })

    # ==== Map to Campaign Action ====
    def map_to_campaign_action(self, request, queryset):
        ids = list(queryset.values_list('pk', flat=True))
        request.session['map_object_ids'] = ids
        return redirect(f'admin:{self.map_view_name}')
    map_to_campaign_action.short_description = "Map to campaign"

    def map_to_campaign_view(self, request):
        selected_ids = request.session.get('map_object_ids', [])
        if not selected_ids:
            self.message_user(request, "No items selected.", level=messages.WARNING)
            return redirect('..')

        if request.method == "POST":
            form = CampaignSelectForm(request.POST)
            if form.is_valid():
                campaign = form.cleaned_data['campaign']
                for obj_id in selected_ids:
                    self.mapping_model.objects.get_or_create(
                        **{self.mapping_fk_name: obj_id, 'campaign': campaign}
                    )
                self.message_user(request, f"Mapped {len(selected_ids)} items to '{campaign.name}'.", level=messages.SUCCESS)
                request.session.pop('map_object_ids', None)
                return redirect('../')
        else:
            form = CampaignSelectForm()

        context = dict(
            self.admin_site.each_context(request),
            title="Map to Campaign",
            form=form,
            selected_count=len(selected_ids),
        )
        return render(request, "admin/map_to_campaign.html", context)


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


@admin.register(Product)
class ProductAdmin(BaselineAdminMixin, admin.ModelAdmin):
    list_display = ('item_name', 'client', 'export_link')
    search_fields = ('item_name',)

    export_view_name = 'product_export_baseline'
    upload_view_name = 'product_upload_baseline'
    map_view_name = 'product_map_to_campaign'
    baseline_table = 'product_baselines'
    id_field = 'ga_product_id'
    mapping_model = Product_Mapping
    mapping_fk_name = 'ga_product_id'


@admin.register(Page)
class PageAdmin(BaselineAdminMixin, admin.ModelAdmin):
    list_display = ('url', 'client', 'export_link')
    search_fields = ('url',)

    export_view_name = 'page_export_baseline'
    upload_view_name = 'page_upload_baseline'
    map_view_name = 'page_map_to_campaign'
    baseline_table = 'page_baselines'
    id_field = 'ga_page_id'
    mapping_model = Page_Mapping
    mapping_fk_name = 'ga_page_id'

    class Media:
        css = {
            'all': ('admin/css/admin_extra.css',)
        }
    
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


