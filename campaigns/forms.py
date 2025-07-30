from django import forms
from .models import Product_Mapping, Page_Mapping, Campaign, Client, ga_page, ga_product

class PageMappingForm(forms.ModelForm):
    client = forms.ModelChoiceField(
        queryset=Client.objects.all(),
        required=False,
        label='Client (for filtering)'
    )

    class Meta:
        model = Page_Mapping
        fields = ['client', 'campaign', 'ga_page']

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

    class Media:
        js = ('campaigns/js/admin_page_mapping.js',)


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
        js = ('campaigns/js/admin_product_mapping.js',)

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