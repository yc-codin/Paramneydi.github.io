from django.shortcuts import render
from django import forms
import requests
from .forms import CompoundInterestForm, InvestmentPhaseForm, CurrencyForm
from decimal import Decimal
from .calculations import (calculate_compound_interest, calculate_lower_bound,
calculate_upper_bound, calculate_with_phases)
from django.http import JsonResponse, HttpResponseRedirect
import logging
import re
from .models import ExchangeRate
from .forms import DateForm
import locale
from django.utils import translation
import math

logger = logging.getLogger(__name__)


def format_currency(value, currency, user_language):
    print(f"DEBUG: Formatting: {value} {currency} for {user_language}")  # Debug
    
    if currency == "TRY" and user_language == 'tr':
        # Formatting number in Turkish style manually
        formatted_value = "{:,.2f}".format(value)
        formatted_value = formatted_value.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"₺{formatted_value}"  
    elif currency == "USD" and user_language == 'en':
        # Formatting number in English style
        return f"${value:,.2f}"
    else:
        # Fallback formatting
        return f"{value:,.2f}"

print(format_currency(36043.75, "TRY", "tr"))  # Should print: 36.043,75₺
print(format_currency(36043.75, "USD", "en"))  # Should print: $36,043.75

def home(request):
    return render(request, 'home.html')


def get_currency_full_name(code):
    mapping = {
        'EUR': 'Euro',
        'USD': 'American Dollar',
        'TRY': 'Turkish Lira',
    }
    return mapping.get(code, '')

def get_currency_short_name(code):
    mapping = {
        'EUR': 'EUR',
        'USD': 'USD',
        'TRY': 'TRY',
    }
    return mapping.get(code, '')

def currency_exchange(request):
    if request.method == 'POST':
        form = CurrencyForm(request.POST)
        if form.is_valid():
            currency_from = form.cleaned_data['currency_from']
            currency_to = form.cleaned_data['currency_to']
            amount = Decimal(form.cleaned_data['amount'])
            try:
                response = requests.get(
                    'https://openexchangerates.org/api/latest.json?app_id=57b99706ca0547d9980afd9918d04722')
                data = response.json()

                if currency_from not in data['rates'] or currency_to not in data['rates']:
                    rate = None
                else:
                    amount = amount if currency_from == 'USD' else amount / Decimal(data['rates'][currency_from])
                    rate = amount * Decimal(data['rates'][currency_to])

            except (requests.exceptions.RequestException, KeyError):
                rate = None

            currency_from_full = get_currency_full_name(currency_from)
            currency_to_full = get_currency_full_name(currency_to)

            currency_from_short = get_currency_short_name(currency_from)
            currency_to_short = get_currency_short_name(currency_to)

            context = {
                'form': form,
                'rate': rate,
                'amount': form.cleaned_data['amount'],
                'currency_from': currency_from,
                'currency_to': currency_to,
                'currency_from_full': currency_from_full,
                'currency_to_full': currency_to_full,
                'currency_from_short': currency_from_short,
                'currency_to_short': currency_to_short
            }
            return render(request, 'kur_cevirme.html', context)

    else:
        form = CurrencyForm()

    context = {
        'form': form,
    }
    return render(request, 'kur_cevirme.html', context)


def compound_interest_view(request):
    user_language = translation.get_language_from_request(request)
    print(f"DEBUG: User Language: {user_language}")  # For debugging
    total_amount_display = lower_bound_display = upper_bound_display = total_spent_display = None
    phases = []
    years = 0
    interest_rate = int('0')
    times_per_year = Decimal('0')
    monthly_contribution = int('0')
    variance = Decimal('0')
    years_as_int = 0 
    principal = int('0')
    end_year = 0  # providing a default value
    print("DEBUG: Initialized variables")  # Add this

    is_ajax_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        print(f"DEBUG: POST Data: {request.POST}")

        raw_principal = request.POST.get('principal', '0')
        print(f"DEBUG: Raw principal: {raw_principal}")  # After Getting Raw Principal
        sanitized_principal = re.sub('[^\d]', '', raw_principal)  # Remove non-digit characters
        print(f"DEBUG: Sanitized principal: {sanitized_principal}")  # After Sanitizing Principal
        principal = Decimal(sanitized_principal or '0')

        raw_monthly_contribution = request.POST.get('monthly_contribution', '0')
        print(f"DEBUG: Raw monthly contribution: {raw_monthly_contribution}")  # After Getting Raw Monthly Contribution
        sanitized_monthly_contribution = re.sub('[^\d,]', '', raw_monthly_contribution).replace(',', '.')
        print(f"DEBUG: Sanitized monthly contribution: {sanitized_monthly_contribution}")  # After Sanitizing Monthly Contribution
        monthly_contribution = Decimal(sanitized_monthly_contribution or '0')
        
        mutable_post = request.POST.copy()  # Make the POST data mutable

        # Sanitize and modify monthly contributions in phases
        total_forms = int(mutable_post.get('phases-TOTAL_FORMS', 0))
        for i in range(total_forms):
            phase_monthly_contribution_key = f'phases-{i}-monthly_contribution'
            raw_phase_monthly_contribution = mutable_post.get(phase_monthly_contribution_key, '0')
            sanitized_phase_monthly_contribution = re.sub('[^0-9.]', '', raw_phase_monthly_contribution)
            phase_monthly_contribution = Decimal(sanitized_phase_monthly_contribution or '0')
            mutable_post[phase_monthly_contribution_key] = str(phase_monthly_contribution)

        mutable_post['principal'] = str(principal)
        mutable_post['monthly_contribution'] = str(monthly_contribution)

        print(f"DEBUG: Mutable POST before form initialization: {mutable_post}")
        form = CompoundInterestForm(mutable_post)
        print(f"DEBUG: Form errors after initialization: {form.errors}")
        years = int(form.cleaned_data.get('years', 0)) if form.is_valid() else 0
        years_as_int = int(years)

        InvestmentPhaseFormSet = forms.formset_factory(InvestmentPhaseForm, extra=0)
        formset = InvestmentPhaseFormSet(mutable_post, prefix='phases', form_kwargs={'years': years_as_int})
        print(f"DEBUG: Formset errors after initialization: {formset.errors}")

        print(f"DEBUG: Mutable POST after sanitization: {mutable_post}")

        if not form.is_valid():
            print("DEBUG: Form errors:", form.errors)

        # Before validating formset, sanitize and modify the monthly contribution in each form

        if form.is_valid() and formset.is_valid():
            print(f"DEBUG: Form cleaned data: {form.cleaned_data}")
            print("Form is valid")
            principal = Decimal(form.cleaned_data.get('principal', '0'))
            print(f"DEBUG: Cleaned principal: {principal}")  # After Validation

            interest_rate = Decimal(form.cleaned_data.get('rate', '0'))
            print(f"DEBUG: Cleaned rate: {interest_rate}")  # After Validation

            times_per_year = int(form.cleaned_data.get('times_per_year', 1))
            print(f"DEBUG: Cleaned times per year: {times_per_year}")  # After Validation

            monthly_contribution = Decimal(form.cleaned_data.get('monthly_contribution', '0'))
            print(f"DEBUG: Cleaned monthly contribution: {monthly_contribution}")  # After Validation

            variance = Decimal(form.cleaned_data.get('variance', '0'))
            print(f"DEBUG: Cleaned variance: {variance}")  # After Validation

            total_amount = calculate_compound_interest(principal, interest_rate, times_per_year, years, monthly_contribution, 0)
            lower_bound = calculate_lower_bound(principal, interest_rate, times_per_year, years, monthly_contribution, variance)
            upper_bound = calculate_upper_bound(principal, interest_rate, times_per_year, years, monthly_contribution, variance)
            total_spent = Decimal(principal) + Decimal(monthly_contribution) * 12 * Decimal(years)
            print("Calculation outputs:", total_amount, total_spent, lower_bound, upper_bound)

            print("DEBUG: Form cleaned data:", form.cleaned_data)

            phases = [
                {
                    'start_year': phase_form.cleaned_data['start_year'],
                    'end_year': phase_form.cleaned_data['end_year'],
                    'interest_rate': phase_form.cleaned_data['interest_rate'],
                    'monthly_contribution': phase_form.cleaned_data['monthly_contribution']
                }
                for phase_form in formset.forms if phase_form.cleaned_data
            ]

            user_language = translation.get_language_from_request(request)

            user_currency = 'TRY' if 'tr' in user_language else 'USD'


            if total_amount is not None:
                total_amount_display = format_currency(total_amount, user_currency, user_language)
            if total_spent is not None:
                total_spent_display = format_currency(total_spent, user_currency, user_language)
            if lower_bound is not None:
                lower_bound_display = format_currency(lower_bound, user_currency, user_language)
            if upper_bound is not None:
                upper_bound_display = format_currency(upper_bound, user_currency, user_language)

            if phases:
                end_year = 0
                for phase in phases:
                    print(f"DEBUG: Processing phase: {phase}")  # During Phases Calculation

                    start_year = int(phase['start_year'])
                    end_year = int(phase['end_year'])
                    monthly_contribution_phase = Decimal(phase['monthly_contribution'])
                    print(
                        f"DEBUG: Monthly contribution for phase: {monthly_contribution_phase}")  # During Phases Calculation
                    total_spent += monthly_contribution_phase * 12 * (end_year - start_year)

                total_spent += Decimal(monthly_contribution) * 12 * (years - end_year)
                lower_bound, total_amount, upper_bound = calculate_with_phases(principal, interest_rate, times_per_year,
                                                                               monthly_contribution, variance, years,
                                                                               phases)

                print(f"DEBUG: Total Amount Calculated: {total_amount}")  # Add this (use actual variable names)
                print(f"DEBUG: Lower Bound Calculated: {lower_bound}")  # Add this
                print(f"DEBUG: Upper Bound Calculated: {upper_bound}")  # Add this
                print(f"DEBUG: Total Spent Calculated: {total_spent}")  # Add this

                if total_amount is not None:
                    total_amount_display = format_currency(total_amount, user_currency, user_language)
                if total_spent is not None:
                    total_spent_display = format_currency(total_spent, user_currency, user_language)
                if lower_bound is not None:
                    lower_bound_display = format_currency(lower_bound, user_currency, user_language)
                if upper_bound is not None:
                    upper_bound_display = format_currency(upper_bound, user_currency, user_language)

                print("Formatted outputs:", total_amount_display, total_spent_display, lower_bound_display, upper_bound_display)

            print(f"Phases: {phases}")

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                response_data = {
                    "total_amount": total_amount_display if total_amount_display is not None else "N/A",
                    "total_spent": total_spent_display if total_spent_display is not None else "N/A",
                    "lower_bound": lower_bound_display if lower_bound_display is not None else "N/A",
                    "upper_bound": upper_bound_display if upper_bound_display is not None else "N/A",
                }
                if not formset.is_valid():
                    response_data['formset_errors'] = formset.errors.as_json()
                print("JSON Response data:", response_data)
                return JsonResponse(response_data)
            else:
                print(f"Form errors: {form.errors}")
                print(f"Formset errors: {formset.errors}")
                total_spent += Decimal(monthly_contribution) * 12 * (years - end_year)
        else:
            print(f"Form errors: {form.errors}")
            print(f"Formset errors: {formset.errors}")
            
        years_as_int = int(years)
        InvestmentPhaseFormSet = forms.formset_factory(InvestmentPhaseForm, extra=0)
        formset = InvestmentPhaseFormSet(prefix='phases', initial=phases, form_kwargs={'years': years_as_int})

        print(f"DEBUG: Re-initialized Formset: {formset}")  # During Re-initialization of Formset

    else:
        print("Handling GET or other request")
        years_as_int = int(years)
        InvestmentPhaseFormSet = forms.formset_factory(InvestmentPhaseForm, extra=0)
        formset = InvestmentPhaseFormSet(prefix='phases', initial=[{} for _ in range(years_as_int)], form_kwargs={'years': years_as_int})

        form = CompoundInterestForm()
        print(f"Initialized Form and Formset for non-POST request: Form: {form}, Formset: {formset}")

    print(f"DEBUG: Total Amount Display: {total_amount_display}")  # Add this
    print(f"DEBUG: Lower Bound Display: {lower_bound_display}")  # Add this
    print(f"DEBUG: Upper Bound Display: {upper_bound_display}")  # Add this
    print(f"DEBUG: Total Spent Display: {total_spent_display}")  # Add this

    context = {
        'form': form,
        'formset': formset,
        'total_amount': total_amount_display,
        'total_spent': total_spent_display,
        'lower_bound': lower_bound_display,
        'upper_bound': upper_bound_display,
    }

    if is_ajax_request:
        data = {
            'total_amount': str(total_amount_display),
            'total_spent': str(total_spent_display),
            'lower_bound': str(lower_bound_display),
            'upper_bound': str(upper_bound_display),
        }
        print(f"DEBUG: Returning JSON data: {data}")  # Debug print statement
        return JsonResponse(data)
    else:
        print(f"DEBUG: Returning HTML response.")  # Debug print statement
        return render(request, 'compound_interest.html', context)

def simple_interest_view(request):
    if request.method == "POST":
        principal = float(request.POST['principal'])
        rate = float(request.POST['rate'])
        time = float(request.POST['time'])
        interest = (principal * rate * time) / 100
        context = {'interest': interest}
    else:
        context = {}

    return render(request, 'simple_interest.html', context)

def forex_compounding_view(request):
    if request.method == "POST":
        principal = float(request.POST['principal'])
        rate = float(request.POST['rate'])
        time = float(request.POST['time'])
        interest = (principal * rate * time) / 100
        context = {'interest': interest}
    else:
        context = {}
    return render(request, 'forex_compounding.html')

def daily_compounding_view(request):
    if request.method == "POST":
        principal = float(request.POST['principal'])
        rate = float(request.POST['rate'])
        time = float(request.POST['time'])
        interest = (principal * rate * time) / 100
        context = {'interest': interest}
    else:
        context = {}
    return render(request, 'daily_compounding.html')


def get_year_choices(request):
    print("DEBUG: Received request at get_year_choices")
    print(f"DEBUG: Request method: {request.method}")
    print("DEBUG: Request GET data:", request.GET)

    year_count_str = request.GET.get('year_count')
    print(f"DEBUG: Extracted year_count_str: {year_count_str}")

    if not year_count_str:
        year_count = 10
    else:
        try:
            year_count = int(year_count_str)
        except ValueError:
            return JsonResponse({'error': 'Invalid year_count value provided'}, status=400)

    form = InvestmentPhaseForm(years=year_count)
    print("DEBUG: Created form with given years")

    start_year_html = str(form['start_year'])
    end_year_html = str(form['end_year'])
    print("DEBUG: Extracted start and end year HTML options")

    return JsonResponse({
        'start_year': start_year_html,
        'end_year': end_year_html
    })


def tufe_bazli_view(request):
    value = None
    if request.method == 'POST':
        form = DateForm(request.POST)
        if form.is_valid():
            year = form.cleaned_data['year']
            month = form.cleaned_data['month']
            try:
                value = ExchangeRate.objects.get(date__year=year, date__month=month).value
            except ExchangeRate.DoesNotExist:
                value = 'Veri bulunamadı.'
    else:
        form = DateForm()

    return render(request, 'tufe_bazli.html', {'form': form, 'value': value})


