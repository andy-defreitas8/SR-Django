from django.urls import path
from .views import client_list, campaign_list, product_mapping_list, page_mapping_list

urlpatterns = [
    path('clients/', client_list, name='client-data'),
    path('campaigns/', campaign_list, name='campaign-data'),
    path('product_mappings/', product_mapping_list, name='product-mapping-data'),
    path('page_mappings/', page_mapping_list, name='page-mapping-data')
]
