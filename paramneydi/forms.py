from django import forms
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

TIMES_PER_YEAR_CHOICES = [
    (1, _('Annually')),
    (2, _('Semiannually')),
    (12, _('Monthly')),
    (365, _('Daily')),
]

class CompoundInterestForm(forms.Form):
    times_per_year = forms.ChoiceField(choices=TIMES_PER_YEAR_CHOICES, label="Times Per Year")
    principal = forms.DecimalField(max_digits=10, decimal_places=2)  # Assuming max_digits as needed
    rate = forms.DecimalField(max_digits=5, decimal_places=2)  # Update decimal places as needed
    years = forms.IntegerField(label="Years")
    monthly_contribution = forms.DecimalField(max_digits=10, decimal_places=2)  # Adjust as needed
    variance = forms.DecimalField(max_digits=5, decimal_places=2)  # Adjust as needed


class YearCountForm(forms.Form):
    years = forms.IntegerField()


class InvestmentPhaseForm(forms.Form):
    interest_rate = forms.FloatField(widget=forms.NumberInput(attrs={'step': 'any'}))
    monthly_contribution = forms.FloatField(
        widget=forms.TextInput(
            attrs={'step': 'any', 'class': 'currency-input', 'id': 'phase_monthly_contribution'}
        )
    )
    start_year = forms.ChoiceField(choices=[])
    end_year = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        years = kwargs.pop('years', None)
        super(InvestmentPhaseForm, self).__init__(*args, **kwargs)

        if years:
            self.fields['start_year'].choices = [('', '-----')] + [(str(i), str(i)) for i in range(0, years)]
            self.fields['end_year'].choices = [('', '-----')] + [(str(i), str(i)) for i in range(1, years + 1)]



class CurrencyForm(forms.Form):
    CHOICES = [
        ('', _("Select a currency")),
        ('EUR', _('Euro')),
        ('USD', _('American Dollar')),
        ('TRY', _('Turkish Lira'))
    ]
    currency_from = forms.ChoiceField(choices=CHOICES, label=_("Currency:"))
    currency_to = forms.ChoiceField(choices=CHOICES, label=_("Currency to Convert:"))
    amount = forms.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], widget=forms.TextInput, label=_("Amount:"))

class DateForm(forms.Form):
    year = forms.IntegerField()
    month = forms.IntegerField()