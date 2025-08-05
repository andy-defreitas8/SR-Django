from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import connection, transaction
import csv
import pandas as pd
import math
from io import TextIOWrapper

from .models import Pricing_Sheet, Station_pricing, Sales_House, Station, Hour, Duration


@admin.register(Pricing_Sheet)
class PricingSheetAdmin(admin.ModelAdmin):
    list_display = ['price_date', 'note']
    change_list_template = "admin/pricing_sheet_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-csv/', self.admin_site.admin_view(self.export_csv_view), name="export_pricing_csv"),
            path('upload-csv/', self.admin_site.admin_view(self.upload_csv_view), name="upload_pricing_csv"),
            path('insert-csv/', self.admin_site.admin_view(self.insert_csv_view), name="insert_pricing_csv"),
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

            try:
                df = pd.read_csv(TextIOWrapper(uploaded_file.file, encoding='utf-8'))

                # Replace blank strings or NaN with None (Python's null equivalent)
                df = df.replace(r'^\s*$', None, regex=True)

                # === ✅ Expected Columns ===
                expected_columns = {
                    'price_date', 'station_name', 'start_hour', 'end_hour',
                    'duration', 'sales_house_name', 'cost_type', 'cost'
                }

                if not expected_columns.issubset(set(df.columns)):
                    missing = expected_columns - set(df.columns)
                    messages.error(request, f"Missing required columns: {', '.join(missing)}")
                    return redirect("admin:upload_pricing_csv")

                # === ✅ Required Field Check ===
                required_fields = ['price_date', 'station_name', 'cost_type', 'cost']
                missing_required = df[required_fields].isnull().any()
                if missing_required.any():
                    missing_cols = missing_required[missing_required == True].index.tolist()
                    messages.error(request, f"Missing required values in columns: {', '.join(missing_cols)}")
                    return redirect("admin:upload_pricing_csv")

                # === ✅ Duration Check ===
                valid_durations = set(Duration.objects.values_list('duration_seconds', flat=True))

                non_null_durations=df['duration'].dropna()
                unknown_durations = set(non_null_durations) - valid_durations

                if unknown_durations:
                    messages.error(request, f"Unknown duration values: {', '.join(map(str, unknown_durations))}")
                    return redirect("admin:upload_pricing_csv")

                # === ✅ Date Format ===
                try:
                    df['price_date'] = pd.to_datetime(df['price_date'], format='%Y-%m-%d').dt.strftime('%Y-%m-%d')
                except ValueError:
                    messages.error(request, "price_date must be in YYYY-MM-DD format.")
                    return redirect("admin:upload_pricing_csv")
                
                # === ✅ Station Name Check ===
                known_stations = dict(Station.objects.values_list('station_name', 'station_id'))
                df['station_id'] = df['station_name'].map(known_stations)
                if df['station_id'].isnull().any():
                    unknown_stations = df[df['station_id'].isnull()]['station_name'].unique()
                    messages.error(request, f"Unknown station names: {', '.join(unknown_stations)}")
                    return redirect("admin:upload_pricing_csv")

                # === ✅ Sales House Name Check ===
                known_sales_houses = dict(Sales_House.objects.values_list('sales_house_name', 'sales_house_id'))

                # Only map non-null values
                df['sales_house_id'] = df['sales_house_name'].apply(
                    lambda x: known_sales_houses.get(x) if pd.notnull(x) else None
                )

                # Check only non-null entries for failed mapping
                invalid_sales_house_rows = df[
                    df['sales_house_name'].notna() & df['sales_house_id'].isna()
                ]

                if not invalid_sales_house_rows.empty:
                    unknown_sales = invalid_sales_house_rows['sales_house_name'].unique()
                    messages.error(request, f"Unknown sales house names: {', '.join(unknown_sales)}")
                    return redirect("admin:upload_pricing_csv")


                # === ✅ Start/End Hour Check ===
                valid_hours = set(Hour.objects.values_list('hour', flat=True))

                invalid_start_hours = set(df['start_hour'].dropna()) - valid_hours
                invalid_end_hours = set(df['end_hour'].dropna()) - valid_hours
                invalid_hours = invalid_start_hours.union(invalid_end_hours)

                if invalid_hours:
                    messages.error(request, f"Unknown hour values: {', '.join(map(str, invalid_hours))}")
                    return redirect("admin:upload_pricing_csv")


                # === ✅ Save cleaned version for insertion ===
                cleaned_data = df[[
                    'price_date', 'station_id', 'start_hour', 'end_hour',
                    'duration', 'sales_house_id', 'cost_type', 'cost'
                ]].to_dict(orient='records')


                request.session['validated_station_pricing'] = cleaned_data
                messages.success(request, f"Successfully validated {len(cleaned_data)} rows. Ready to insert.")
                return redirect("admin:upload_pricing_csv")

            except Exception as e:
                messages.error(request, f"An error occurred while processing the CSV: {str(e)}")
                return redirect("admin:upload_pricing_csv")

        return render(request, "admin/upload_csv_form.html", {})

    def insert_csv_view(self, request):
        if request.method != "POST":
            messages.error(request, "Invalid request method.")
            return redirect("admin:upload_pricing_csv")

        validated_data = request.session.get("validated_station_pricing")

        if not validated_data:
            messages.error(request, "No validated data available. Please upload and validate a CSV first.")
            return redirect("admin:upload_pricing_csv")

        try:
            # === ✅ Convert NaN to None for nullable fields ===
            for row in validated_data:
                for field in ['start_hour', 'end_hour', 'duration', 'sales_house_id']:
                    if pd.isna(row.get(field)):
                        row[field] = None

            # === ✅ Build model instances ===
            instances = []
            for row in validated_data:
                instance = Station_pricing(
                    price_date_id=row['price_date'],           # FK to Pricing_Sheet
                    station_id=row['station_id'],              # FK to Station
                    start_hour_id=row['start_hour'],           # FK to Hour (nullable)
                    end_hour_id=row['end_hour'],               # FK to Hour (nullable)
                    duration_id=row['duration'],               # FK to Duration (nullable)
                    sales_house_id=row.get('sales_house_id'),  # FK to Sales_House (nullable)
                    cost_type=row['cost_type'],
                    cost=row['cost']
                )
                instances.append(instance)

            # === ✅ Bulk insert with transaction ===
            with transaction.atomic():
                Station_pricing.objects.bulk_create(instances, batch_size=1000)

            # === ✅ Clean up ===
            del request.session['validated_station_pricing']
            messages.success(request, f"Successfully inserted {len(instances)} new station pricing records.")
            return redirect("admin:upload_pricing_csv")

        except Exception as e:
            messages.error(request, f"An error occurred during insertion: {str(e)}")
            return redirect("admin:upload_pricing_csv")


@admin.register(Station_pricing)
class StationPricingAdmin(admin.ModelAdmin):
    list_display = ['price_date', 'station', 'start_hour', 'end_hour', 'duration', 'sales_house', 'cost_type', 'cost']
    list_filter = ['price_date']

