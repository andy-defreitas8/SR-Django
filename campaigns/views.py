from django.shortcuts import render
from .models import Client, Campaign, Product_Mapping, Page_Mapping

def client_list(request):
    rows = Client.objects.all()
    return render(request, 'client_list.html', {'rows': rows})

def campaign_list(request):
    rows = Campaign.objects.all()
    return render(request, 'campaign_list.html', {'rows': rows})

def product_mapping_list(request):
    rows = Product_Mapping.objects.all()
    return render(request, 'product_mapping_list.html', {'rows': rows})

def page_mapping_list(request):
    rows = Page_Mapping.objects.all()
    return render(request, 'page_mapping_list.html', {'rows': rows})