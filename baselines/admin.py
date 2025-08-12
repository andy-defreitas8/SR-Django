from django.contrib import admin, messages
from django.urls import path
from django.http import HttpResponse
from django.db import connection
from django.utils.html import format_html
from django.shortcuts import redirect, render
import csv
from io import TextIOWrapper
import pandas as pd

from .models import Product, Page


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'ga_product_id', 'client', 'export_link')
    readonly_fields = ('export_link',)
    search_fields = ('item_name',)

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
            path(
                '<path:object_id>/change/upload-baseline/',
                self.admin_site.admin_view(self.upload_csv_view),
                name="upload_product_baseline_csv"
            ),
        ]
        return custom_urls + urls

    def export_link(self, obj):
        return format_html(
            '<a class="button" href="{}/change/export-baseline/">Export Baseline CSV</a>&nbsp;'
            '<a class="button" href="{}/change/upload-baseline/">Upload CSV</a>',
            obj.pk, obj.pk
        )
    export_link.short_description = "Export/Upload Baseline"

    def export_baseline(self, request, object_id):
        """Exports the baseline data for a specific product using raw SQL."""
        product = Product.objects.get(pk=object_id)

        # Query from product_baselines table
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT day_of_week, hour_of_day, baseline_session, baseline_sales
                FROM product_baselines
                WHERE ga_product_id = %s
                ORDER BY day_of_week, hour_of_day
            """, [product.ga_product_id])
            rows = cursor.fetchall()

        # Build CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{product.item_name}_baseline.csv"'
        writer = csv.writer(response)
        writer.writerow(['item_name', 'day_of_week', 'hour_of_day', 'baseline_session', 'baseline_sales'])
        for row in rows:
            writer.writerow([product.item_name] + list(row))

        return response
    
    def upload_csv_view(self, request, object_id):

        product = Product.objects.get(pk=object_id)
        if request.method == "POST":
            uploaded_file = request.FILES.get("csv_file")

            if not uploaded_file:
                messages.error(request, "No file was uploaded.")
                return redirect("admin:upload_product_baseline_csv", object_id=object_id)

            if not uploaded_file.name.lower().endswith('.csv'):
                messages.error(request, "The uploaded file must be a .csv file.")
                return redirect("admin:upload_product_baseline_csv", object_id=object_id)
            
            try:
                df = pd.read_csv(TextIOWrapper(uploaded_file.file, encoding='utf-8'))

                expected_columns = {
                    'item_name', 'day_of_week', 'hour_of_day', 'baseline_session', 'baseline_sales'
                }

                if not expected_columns.issubset(set(df.columns)):
                    missing = expected_columns - set(df.columns)
                    messages.error(request, f"Missing required columns: {', '.join(missing)}")
                    return redirect("admin:upload_product_baseline_csv", object_id=object_id)
                
                required_fields = ['item_name', 'day_of_week', 'hour_of_day', 'baseline_session', 'baseline_sales']
                missing_required = df[required_fields].isnull().any()
                if missing_required.any():
                    missing_cols = missing_required[missing_required == True].index.tolist()
                    messages.error(request, f"Missing required values in columns: {', '.join(missing_cols)}")
                    return redirect("admin:upload_product_baseline_csv", object_id=object_id)
                
                known_products = dict(Product.objects.values_list('item_name', 'ga_product_id'))
                df['ga_product_id'] = df['item_name'].map(known_products)
                if df['ga_product_id'].isnull().any():
                    unknown_products = df[df['ga_product_id'].isnull()]['item_name'].unique()
                    product_list = Product.objects.values_list('item_name', flat=True).order_by('item_name')
                    messages.error(
                        request,
                        f"Unknown product name(s): {', '.join(unknown_products)}"
                    )

                    return redirect("admin:upload_product_baseline_csv", object_id=object_id)
                
                cleaned_data = df[[
                    'ga_product_id', 'day_of_week', 'hour_of_day', 'baseline_session', 'baseline_sales'
                ]].to_dict(orient='records')

                request.session['validated_product_baseline'] = cleaned_data
                messages.success(request, f"Successfully validated {len(cleaned_data)} rows. Ready to insert.")
                return redirect("admin:upload_product_baseline_csv", object_id=object_id)
            
            except Exception as e:
                messages.error(request, f"An error occurred while processing the CSV: {str(e)}")
                return redirect("admin:upload_product_baseline_csv", object_id=object_id)

        return render(request, "admin/upload_product_csv.html", {"product": product})
    
@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('url', 'ga_page_id', 'export_link')
    readonly_fields = ('export_link',)
    search_fields = ('url',)

    class Media:
        css = {
            'all': ('baselines/admin_extra.css',)
        }

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
            path(
                '<path:object_id>/change/upload-baseline/',
                self.admin_site.admin_view(self.upload_csv_view),
                name="upload_page_baseline_csv"
            ),
        ]
        return custom_urls + urls

    def export_link(self, obj):
        return format_html(
            '<a class="button" href="{}/change/export-baseline/">Export Baseline CSV</a>&nbsp;'
            '<a class="button" href="{}/change/upload-baseline/">Upload CSV</a>',
            obj.pk, obj.pk
        )
    export_link.short_description = "Export/Upload Baseline"

    def export_baseline(self, request, object_id):
        """Exports the baseline data for a specific page using raw SQL."""
        page = Page.objects.get(pk=object_id)

        # Query from page_baselines table
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

    def upload_csv_view(self, request, object_id):
        page = Page.objects.get(pk=object_id)
        if request.method == "POST":
            uploaded_file = request.FILES.get("csv_file")

            if not uploaded_file:
                messages.error(request, "No file was uploaded.")
                return redirect("admin:upload_page_baseline_csv", object_id=object_id)

            if not uploaded_file.name.lower().endswith('.csv'):
                messages.error(request, "The uploaded file must be a .csv file.")
                return redirect("admin:upload_page_baseline_csv", object_id=object_id)
            
            try:
                df = pd.read_csv(TextIOWrapper(uploaded_file.file, encoding='utf-8'))

                expected_columns = {
                    'url', 'day_of_week', 'hour_of_day', 'baseline_session', 'baseline_sales'
                }

                if not expected_columns.issubset(set(df.columns)):
                    missing = expected_columns - set(df.columns)
                    messages.error(request, f"Missing required columns: {', '.join(missing)}")
                    return redirect("admin:upload_page_baseline_csv", object_id=object_id)
                
                required_fields = ['url', 'day_of_week', 'hour_of_day', 'baseline_session', 'baseline_sales']
                missing_required = df[required_fields].isnull().any()
                if missing_required.any():
                    missing_cols = missing_required[missing_required == True].index.tolist()
                    messages.error(request, f"Missing required values in columns: {', '.join(missing_cols)}")
                    return redirect("admin:upload_page_baseline_csv", object_id=object_id)
                
                # Map url to ga_page_id
                known_pages = dict(Page.objects.values_list('url', 'ga_page_id'))
                df['ga_page_id'] = df['url'].map(known_pages)
                if df['ga_page_id'].isnull().any():
                    unknown_urls = df[df['ga_page_id'].isnull()]['url'].unique()
                    messages.error(
                        request,
                        f"Unknown url(s): {', '.join(map(str, unknown_urls))}"
                    )
                    return redirect("admin:upload_page_baseline_csv", object_id=object_id)
                
                cleaned_data = df[{
                    'ga_page_id', 'day_of_week', 'hour_of_day', 'baseline_session', 'baseline_sales'
                }].to_dict(orient='records')

                request.session['validated_page_baseline'] = cleaned_data
                messages.success(request, f"Successfully validated {len(cleaned_data)} rows. Ready to insert.")
                return redirect("admin:upload_page_baseline_csv", object_id=object_id)
            
            except Exception as e:
                messages.error(request, f"An error occurred while processing the CSV: {str(e)}")
                return redirect("admin:upload_page_baseline_csv", object_id=object_id)

        return render(request, "admin/upload_page_csv.html", {"page": page})
