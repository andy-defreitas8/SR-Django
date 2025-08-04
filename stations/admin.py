from django.contrib import admin
from django.urls import path
from django.shortcuts import render
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
            path('export-csv/', self.admin_site.admin_view(self.export_csv_view), name="export_pricing_csv")
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
 

@admin.register(Station_pricing)
class StationPricingAdmin(admin.ModelAdmin):
    list_display = ['price_date', 'station', 'start_hour', 'end_hour', 'duration', 'sales_house', 'cost_type', 'cost']
    list_filter = ['price_date']

