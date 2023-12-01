from decimal import Decimal, getcontext
import random


getcontext().prec = 6
def calculate_compound_interest(principal, interest_rate, times_per_year, years, monthly_contribution, variance):
    print(f"DEBUG: calculate_compound_interest inputs: {locals()}")
    interest_rate = Decimal(interest_rate) / 100
    amount = Decimal(principal)
    monthly_contribution = Decimal(monthly_contribution)
    for year in range(years):
        for _ in range(times_per_year):
            amount += amount * (interest_rate / times_per_year)
        amount += monthly_contribution * 12
    print(f"DEBUG: calculate_compound_interest output: {amount}")
    return amount

def calculate_lower_bound(principal, interest_rate, times_per_year, years, monthly_contribution, variance):
    interest_rate = Decimal(interest_rate) / 100
    variance = Decimal(variance) / 100
    amount = Decimal(principal)
    monthly_contribution = Decimal(monthly_contribution)
    for year in range(years):
        for _ in range(times_per_year):
            amount += amount * ((interest_rate - variance) / times_per_year)
        amount += monthly_contribution * 12
    return amount

def calculate_upper_bound(principal, interest_rate, times_per_year, years, monthly_contribution, variance):
    interest_rate = Decimal(interest_rate) / 100
    variance = Decimal(variance) / 100
    amount = Decimal(principal)
    monthly_contribution = Decimal(monthly_contribution)
    for year in range(years):
        for _ in range(times_per_year):
            amount += amount * ((interest_rate + variance) / times_per_year)
        amount += monthly_contribution * 12
    return amount


def calculate_with_phases(principal, interest_rate, times_per_year, monthly_contribution, variance, years, phases=None):
    print(f"DEBUG: calculate_with_phases inputs: {locals()}")
    interest_rate = Decimal(interest_rate) / 100
    variance = Decimal(variance) / 100
    avg_amount = Decimal(principal)
    min_amount = Decimal(principal)
    max_amount = Decimal(principal)
    monthly_contribution = Decimal(monthly_contribution)

    for year in range(years):
        phase = next((phase for phase in phases if int(phase['start_year']) <= year < int(phase['end_year'])),
                     None) if phases else None

        if phase:
            current_interest_rate = Decimal(phase['interest_rate']) / 100
            current_monthly_contribution = Decimal(phase['monthly_contribution'])
        else:
            current_interest_rate = interest_rate
            current_monthly_contribution = monthly_contribution

        yearly_contribution = current_monthly_contribution * 12

        for _ in range(times_per_year):
            avg_amount += avg_amount * (current_interest_rate / times_per_year)
            min_amount += min_amount * ((current_interest_rate - variance) / times_per_year)
            max_amount += max_amount * ((current_interest_rate + variance) / times_per_year)

        avg_amount += yearly_contribution / times_per_year
        min_amount += yearly_contribution / times_per_year
        max_amount += yearly_contribution / times_per_year

        print(f"DEBUG: At end of Year {year}:")
        print(f"Min Amount: {min_amount}")
        print(f"Avg Amount: {avg_amount}")
        print(f"Max Amount: {max_amount}\n")

    print(f"DEBUG: calculate_with_phases output: {min_amount}, {avg_amount}, {max_amount}")
    return min_amount, avg_amount, max_amount