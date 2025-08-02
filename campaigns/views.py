from django.shortcuts import render
from django.http import JsonResponse
from .models import Client, Campaign, Product_Mapping, Page_Mapping, ga_product, ga_page

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

def get_filtered_options(request):
    client_id = request.GET.get('client_id')
    print(f"[DEBUG] Client ID received: {client_id}")

    products = ga_product.objects.filter(client_id=client_id).values('ga_product_id', 'product_name')
    pages = ga_page.objects.filter(client_id=client_id).values('ga_page_id', 'url')

    return JsonResponse({
        'products': list(products),
        'pages': list(pages),
    })
