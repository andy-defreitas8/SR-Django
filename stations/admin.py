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

                # === ✅ Parse and validate price_date column ===
                try:
                    df['price_date'] = pd.to_datetime(df['price_date'], dayfirst=True, errors='coerce')
                    if df['price_date'].isnull().any():
                        messages.error(request, "One or more rows have invalid date formats. Please use DD/MM/YYYY or YYYY-MM-DD.")
                        return redirect("admin:upload_pricing_csv")

                    # Standardize to YYYY-MM-DD for matching
                    df['price_date'] = df['price_date'].dt.strftime('%Y-%m-%d')
                except Exception as e:
                    messages.error(request, f"Failed to parse dates: {str(e)}")
                    return redirect("admin:upload_pricing_csv")
                
                # === ✅ Station Name Check ===
                known_stations = dict(Station.objects.values_list('station_name', 'station_id'))
                df['station_id'] = df['station_name'].map(known_stations)
                if df['station_id'].isnull().any():
                    unknown_stations = df[df['station_id'].isnull()]['station_name'].unique()
                    station_list = Station.objects.values_list('station_name', flat=True).order_by('station_name')
                    messages.error(
                        request,
                        f"Unknown station name(s): {', '.join(unknown_stations)}"
                    )

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

            # === ✅ Extract the single price_date for this batch ===
            price_date = validated_data[0]['price_date']

            # === ✅ Ensure Pricing_Sheet exists for this date ===
            _, created = Pricing_Sheet.objects.get_or_create(price_date=price_date)

            if created:
                messages.info(request, f"Pricing sheet for {price_date} was automatically created.")

            # === ✅ Fetch existing records for that price_date ===
            existing_rows = Station_pricing.objects.filter(price_date=price_date).values(
                'price_date',
                'station_id',
                'start_hour',
                'end_hour',
                'duration',
                'sales_house_id',
                'cost_type',
                'cost'
            )

            # === ✅ Normalize existing rows for comparison ===
            existing_set = {
                (
                    str(row['price_date']),
                    int(row['station_id']),
                    int(row['start_hour']) if row['start_hour'] is not None else None,
                    int(row['end_hour']) if row['end_hour'] is not None else None,
                    int(row['duration']) if row['duration'] is not None else None,
                    int(row['sales_house_id']) if row['sales_house_id'] is not None else None,
                    str(row['cost_type']),
                    float(row['cost'])
                )
                for row in existing_rows
            }

            # === ✅ Filter and normalize input rows ===
            rows_to_insert = []
            for row in validated_data:
                row_tuple = (
                    str(row['price_date']),
                    int(row['station_id']),
                    int(row.get('start_hour')) if row.get('start_hour') is not None else None,
                    int(row.get('end_hour')) if row.get('end_hour') is not None else None,
                    int(row.get('duration')) if row.get('duration') is not None else None,
                    int(row.get('sales_house_id')) if row.get('sales_house_id') is not None else None,
                    str(row['cost_type']),
                    float(row['cost'])
                )
                if row_tuple not in existing_set:
                    rows_to_insert.append(row)

            if not rows_to_insert:
                messages.info(request, "No new records to insert. All rows already exist.")
                return redirect("admin:upload_pricing_csv")

            # === ✅ Build model instances ===
            instances = [
                Station_pricing(
                    price_date_id=row['price_date'],
                    station_id=row['station_id'],
                    start_hour_id=int(row.get('start_hour')) if row.get('start_hour') is not None else None,
                    end_hour_id=int(row.get('end_hour')) if row.get('end_hour') is not None else None,
                    duration_id=int(row.get('duration')) if row.get('duration') is not None else None,
                    sales_house_id=row.get('sales_house_id') if row.get('sales_house_id') is not None else None,
                    cost_type=row['cost_type'],
                    cost=row['cost']
                )
                for row in rows_to_insert
            ]

            # === ✅ Insert with transaction ===
            with transaction.atomic():
                Station_pricing.objects.bulk_create(instances, batch_size=1000)

            # === ✅ Clean up and feedback ===
            del request.session['validated_station_pricing']
            messages.success(
                request,
                f"Inserted {len(instances)} new rows. {len(validated_data) - len(instances)} duplicates were skipped."
            )
            return redirect("admin:upload_pricing_csv")

        except Exception as e:
            messages.error(request, f"An error occurred during insertion: {str(e)}")
            return redirect("admin:upload_pricing_csv")



@admin.register(Station_pricing)
class StationPricingAdmin(admin.ModelAdmin):
    list_display = ['price_date', 'station', 'start_hour', 'end_hour', 'duration', 'sales_house', 'cost_type', 'cost']
    list_filter = ['price_date']

