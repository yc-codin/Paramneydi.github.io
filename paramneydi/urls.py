from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('kur_cevirme/', views.currency_exchange, name='currency_exchange'),
    path('compound_interest/', views.compound_interest_view, name='compound_interest_view'),
    path('simple_interest/', views.simple_interest_view, name='simple_interest_view'),
    path('forex_compounding/', views.forex_compounding_view, name='forex_compounding_view'),
    path('daily_compounding/', views.daily_compounding_view, name='daily_compounding_view'),
    path('i18n/', include('django.conf.urls.i18n')),
    path('get_year_choices/', views.get_year_choices, name='get_year_choices'),
    path('tufe-bazli/', views.tufe_bazli_view, name='tufe_bazli')  # Correctly reference tufe_bazli_view from views module
]
