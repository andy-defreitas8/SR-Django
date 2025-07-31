from django import forms
from .models import Product_Mapping, Page_Mapping, Campaign, Client, ga_page, ga_product, Commercial


# class CampaignForm(forms.ModelForm):
#     product = forms.ModelChoiceField(
#         queryset=ga_product.objects.none(),
#         required=False,
#         label="Product to Map"
#     )

#     page = forms.ModelChoiceField(
#         queryset=ga_page.objects.none(),
#         required=False,
#         label="Page to Map"
#     )

#     commercial = forms.ModelChoiceField(
#         queryset=Commercial.objects.all(),
#         required=False,
#         label="Commercial to Map"
#     )

#     class Meta:
#         model = Campaign
#         fields = ['client', 'name', 'product', 'page', 'commercial']

#     class Media:
#         js = ('campaigns/js/client_filtering.js',)

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         client_id = None

#         if 'client' in self.data:
#             try:
#                 client_id = int(self.data.get('client'))
#             except (ValueError, TypeError):
#                 pass
#         elif self.instance.pk:
#             try:
#                 client_id = self.instance.client.client_id
#             except AttributeError:
#                 pass


#         if client_id:
#             self.initial['client'] = client_id
#             self.fields['product'].queryset = ga_product.objects.filter(client_id=client_id)
#             self.fields['page'].queryset = ga_page.objects.filter(client_id=client_id)
#         else:
#             self.fields['product'].queryset = ga_product.objects.none()
#             self.fields['page'].queryset = ga_page.objects.none()  


class PageMappingForm(forms.ModelForm):
    client = forms.ModelChoiceField(
        queryset=Client.objects.all(),
        required=False,
        label='Client (for filtering)'
    )

    class Meta:
        model = Page_Mapping
        fields = ['client', 'campaign', 'ga_page']

    class Media:
        js = ('campaigns/js/client_filtering.js',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['campaign'].queryset = Campaign.objects.none()
        self.fields['ga_page'].queryset = ga_page.objects.none()

        client_id = None

        # From submitted data
        if 'client' in self.data:
            try:
                client_id = int(self.data.get('client'))
            except (ValueError, TypeError):
                client_id = None

        # From existing instance
        elif self.instance.pk:
            try:
                client_id = self.instance.campaign.client.client_id
            except AttributeError:
                client_id = None

        if client_id:
            self.initial['client'] = client_id
            self.fields['campaign'].queryset = Campaign.objects.filter(client_id=client_id)
            self.fields['ga_page'].queryset = ga_page.objects.filter(client_id=client_id)


class ProductMappingForm(forms.ModelForm):
    client = forms.ModelChoiceField(
        queryset=Client.objects.all(),
        required=False,
        label='Client (for filtering)'
    )

    class Meta:
        model = Product_Mapping
        fields = ['client', 'campaign', 'ga_product']

    class Media:
        js = ('campaigns/js/client_filtering.js',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Start with empty querysets
        self.fields['campaign'].queryset = Campaign.objects.none()
        self.fields['ga_product'].queryset = ga_product.objects.none()

        client_id = None

        print("client_id resolved to:", client_id)
        print("ga_product queryset size:", self.fields['ga_product'].queryset.count())

        # Case 1: from submitted form data (e.g. user selected client)
        if 'client' in self.data:
            try:
                client_id = int(self.data.get('client'))
            except (ValueError, TypeError):
                client_id = None

        # Case 2: from existing instance (editing)
        elif self.instance.pk:
            try:
                client_id = self.instance.campaign.client.client_id
            except AttributeError:
                client_id = None

        # Set initial so it’s retained in the form
        if client_id:
            self.initial['client'] = client_id
            self.fields['campaign'].queryset = Campaign.objects.filter(client_id=client_id)
            self.fields['ga_product'].queryset = ga_product.objects.filter(client_id=client_id)
        else:
            self.fields['campaign'].queryset = Campaign.objects.none()
            self.fields['ga_product'].queryset = ga_product.objects.none()