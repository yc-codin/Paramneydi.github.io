from django.shortcuts import render
import requests
from .forms import CurrencyForm

def home(request):
    if request.method == 'POST':
        form = CurrencyForm(request.POST)
        if form.is_valid():
            currency_from = form.cleaned_data['currency_from']
            currency_to = form.cleaned_data['currency_to']
            amount = form.cleaned_data['amount']

            try:
                response = requests.get(
                    'https://openexchangerates.org/api/latest.json?app_id=your-app-id')
                data = response.json()

                if currency_from == currency_to:
                    rate = amount
                else:
                    rate = (amount * data['rates'][currency_to]) / data['rates'][currency_from]

            except requests.exceptions.RequestException:
                rate = None

            context = {
                'form': form,
                'rate': rate,
            }
            return render(request, 'index.html', context)

    else:
        form = CurrencyForm()

    context = {
        'form': form,
    }
    return render(request, 'index.html', context)
