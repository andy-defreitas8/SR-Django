from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from django.db import connection
from django.utils.html import format_html
import csv

from .models import Product, Page


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'ga_product_id', 'export_link')
    readonly_fields = ('export_link',)

    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/change/export-baseline/',
                self.admin_site.admin_view(self.export_baseline),
                name="product_export_baseline"
            ),
        ]
        return custom_urls + urls

    def export_link(self, obj):
        return format_html(
            '<a class="button" href="{}/change/export-baseline/">Export Baseline CSV</a>',
            obj.pk
        )
    export_link.short_description = "Export Baseline"

    def export_baseline(self, request, object_id):
        """Exports the baseline data for a specific product using raw SQL."""
        product = Product.objects.get(pk=object_id)

        # Query from product_baselines table
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT ga_product_id, day_of_week, hour_of_day, baseline_session, baseline_sales
                FROM product_baselines
                WHERE ga_product_id = %s
                ORDER BY day_of_week, hour_of_day
            """, [product.ga_product_id])
            rows = cursor.fetchall()

        # Build CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{product.item_name}_baseline.csv"'
        writer = csv.writer(response)
        writer.writerow(['ga_product_id', 'day_of_week', 'hour_of_day', 'baseline_session', 'baseline_sales'])
        for row in rows:
            writer.writerow(row)

        return response
    
@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('url', 'ga_page_id', 'export_link')
    readonly_fields = ('export_link',)

    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/change/export-baseline/',
                self.admin_site.admin_view(self.export_baseline),
                name="page_export_baseline"
            ),
        ]
        return custom_urls + urls

    def export_link(self, obj):
        return format_html(
            '<a class="button" href="{}/change/export-baseline/">Export Baseline CSV</a>',
            obj.pk
        )
    export_link.short_description = "Export Baseline"

    def export_baseline(self, request, object_id):
        """Exports the baseline data for a specific page using raw SQL."""
        page = Page.objects.get(pk=object_id)

        # Query from product_baselines table
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT ga_page_id, day_of_week, hour_of_day, baseline_session, baseline_sales
                FROM page_baselines
                WHERE ga_page_id = %s
                ORDER BY day_of_week, hour_of_day
            """, [page.ga_page_id])
            rows = cursor.fetchall()

        # Build CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{page.url}_baseline.csv"'
        writer = csv.writer(response)
        writer.writerow(['ga_page_id', 'day_of_week', 'hour_of_day', 'baseline_session', 'baseline_sales'])
        for row in rows:
            writer.writerow(row)

        return response
