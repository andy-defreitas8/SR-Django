from django import forms
from .models import Product_Mapping, Page_Mapping, Campaign, Client, ga_page, ga_product, Commercial


class CommercialInlineForm(forms.ModelForm):
    commercial = forms.ModelChoiceField(
        queryset=Commercial.objects.filter(campaign__isnull=True),
        required=False,
        label="Select Commercial by Title"
    )

    class Meta:
        model = Commercial
        fields = []  # no real model fields shown

    def save(self, commit=True):
        selected_commercial = self.cleaned_data.get('commercial')
        if selected_commercial:
            selected_commercial.campaign = self.instance.campaign
            selected_commercial.save()
        return selected_commercial




