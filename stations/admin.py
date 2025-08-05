from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import connection
import csv

from .models import Pricing_Sheet, Station_pricing


@admin.register(Pricing_Sheet)
class PricingSheetAdmin(admin.ModelAdmin):
    list_display = ['price_date', 'note']
    change_list_template = "admin/pricing_sheet_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-csv/', self.admin_site.admin_view(self.export_csv_view), name="export_pricing_csv"),
            path('upload-csv/', self.admin_site.admin_view(self.upload_csv_view), name="upload_pricing_csv")
        ]
        return custom_urls + urls

    def export_csv_view(self, request):
        if request.method == 'POST':
            selected_date = request.POST.get('price_date')

            sql = """
                SELECT 
                    sp.price_date,
                    s.station_name,
                    sh.hour AS start_hour,
                    eh.hour AS end_hour,
                    sp.duration,
                    shs.sales_house_name,
                    sp.cost_type,
                    sp.cost
                FROM sr_station_prices sp
                LEFT JOIN sr_exclusive.sr_stations s ON s.station_id = sp.station_id
                LEFT JOIN sr_exclusive.hours sh ON sh.hour = sp.start_hour
                LEFT JOIN sr_exclusive.hours eh ON eh.hour = sp.end_hour
                LEFT JOIN sr_exclusive.sr_sales_houses shs ON shs.sales_house_id = sp.sales_house_id
                WHERE sp.price_date = '2025-08-01'
                ORDER BY sp.price_id;
            """

            with connection.cursor() as cursor:
                cursor.execute(sql, [selected_date])
                rows = cursor.fetchall()

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="station_prices_{selected_date}.csv"'

            writer = csv.writer(response)
            writer.writerow([
                'price_date', 'station_name', 'start_hour', 'end_hour',
                'duration', 'sales_house_name', 'cost_type', 'cost'
            ])
            for row in rows:
                writer.writerow(row)

            return response

        # Show the dropdown form
        all_dates = Pricing_Sheet.objects.values_list('price_date', flat=True).order_by('-price_date')
        return render(request, 'admin/export_csv_form.html', {'dates': all_dates})
    
    def upload_csv_view(self, request):
        if request.method == "POST":
            uploaded_file = request.FILES.get("csv_file")
            if not uploaded_file:
                messages.error(request, "No file was uploaded.")
                return redirect("admin:upload_pricing_csv")
            
            if not uploaded_file.name.lower().endswith('.csv'):
                messages.error(request, "The uploaded file must be a .csv file.")
                return redirect("admin:upload_pricing_csv")

            request.session['uploaded_filename'] = uploaded_file.name

            # Success placeholder
            messages.success(request, f"File '{uploaded_file.name}' uploaded. (Validation to be implemented.)")
            return redirect("admin:upload_pricing_csv")

        return render(request, "admin/upload_csv_form.html", {})
 

@admin.register(Station_pricing)
class StationPricingAdmin(admin.ModelAdmin):
    list_display = ['price_date', 'station', 'start_hour', 'end_hour', 'duration', 'sales_house', 'cost_type', 'cost']
    list_filter = ['price_date']

