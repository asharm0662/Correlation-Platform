from django.shortcuts import render
from django.db.models import Avg
from django.core.serializers.json import DjangoJSONEncoder
from models import DataSource
from datetime import datetime
from scipy.stats.stats import pearsonr
from get_api_data import get_api_data
import numpy as np
import itertools
import json


def index(request):
    data_sources = DataSource.objects.all()
    context = {
        'data_sources': data_sources.filter(data_type='index rates'),
        'currency_list': [
            "AUD",
            "CAD",
            "CHF",
            "CYP",
            "CZK",
            "DKK",
            "EEK",
            "EUR",
            "GBP",
            "HKD",
            "HUF",
            "ISK",
            "JPY",
            "KRW",
            "LTL",
            "LVL",
            "MTL",
            "NOK",
            "NZD",
            "PLN",
            "ROL",
            "SEK",
            "SGD",
            "SIT",
            "SKK",
            "TRL",
            "USD",
            "ZAR",
        ],
    }

    if request.method == 'POST':
        if request.POST['analyze'] == 'cancel':
            return render(request, 'dashboard/index.html', context)

        # Get currency types
        try:
            first_currency = request.POST['first_currency']
            second_currency = request.POST['second_currency']
            if first_currency not in context['currency_list'] or second_currency not in context['currency_list']:
                context['error'] = "Failed to load the data! Please select Exchange rate."
                return render(request, 'dashboard/index.html', context)

        except KeyError:
            context['error'] = "Failed to load the data! Please select Exchange rate."
            return render(request, 'dashboard/index.html', context)

        # Get index type
        try:
            index_rate = data_sources.get(human_name=request.POST['index_rate'])

        except (KeyError, DataSource.DoesNotExist):
            context['error'] = "Failed to load the data! Please select Index Rate."
            return render(request, 'dashboard/index.html', context)

        # Get the date range
        try:
            date_input = request.POST['date_input'].strip()
            splitted_date = [x.strip() for x in date_input.split('-')]
            lower_date = datetime.strptime(splitted_date[0], "%m/%d/%Y").date()
            higher_date = datetime.strptime(splitted_date[1], "%m/%d/%Y").date()
            # lower_date = date(lower_date.year, lower_date.month, lower_date.day)
            # higher_date = date(higher_date.year, higher_date.month, higher_date.day)

        except (IndexError, ValueError):
            context['error'] = "Failed to load the data! Invalid date format."
            return render(request, 'dashboard/index.html', context)

        # Get the data sets from db and api
        data_set_currency = get_api_data(first_currency, second_currency, lower_date, higher_date)
        data_set_index_rate = index_rate.dateddata_set.filter(date__gte=lower_date).filter(
            date__lte=higher_date).order_by('date')
        data_set_sentiment_score = DataSource.objects.get(name='sentiment_score').sentimentdata_set.all()

        if not data_set_currency or not data_set_index_rate:
            context['error'] = "Failed to load the data! No data in this time period."
            return render(request, 'dashboard/index.html', context)

        # Get the headers for the table
        context['exchange_rate'] = "{0}/{1} Exchange rate".format(first_currency, second_currency)
        context['index_rate'] = index_rate.human_name

        # Start populating context for the table and vectors for the chart and correlation coefficients
        context['data'] = list()
        data_vector_exchange_rate = list()
        data_vector_index_rate = list()
        data_vector_sentiment_score = list()
        date_vector = list()
        for data_exchange_rate, data_index_rate, data_sentiment_score in itertools.izip(data_set_currency,
                                                                                        data_set_index_rate,
                                                                                        data_set_sentiment_score):
            temp_dict = dict()
            temp_dict['date'] = data_exchange_rate['date']
            temp_dict['exchange_rate'] = data_exchange_rate['value']
            temp_dict['index_rate'] = data_index_rate.value
            context['data'].append(temp_dict)
            data_vector_exchange_rate.append(data_exchange_rate['value'])
            data_vector_index_rate.append(data_index_rate.value)
            data_vector_sentiment_score.append(data_sentiment_score.value)
            date_vector.append(str(temp_dict['date']))

        # Populating context for the charts
        context['chart'] = dict()
        context['chart']['date_vector'] = date_vector
        context['chart']['data_vector_exchange_rate'] = data_vector_exchange_rate
        context['chart']['data_vector_index_rate'] = data_vector_index_rate

        # Start populating context for math functions and sentiment score
        context['solution'] = dict()
        context['solution']['sentiment_score'] = data_set_sentiment_score.aggregate(Avg('value'))['value__avg']
        context['solution']['date_input'] = date_input

        if request.POST.get('correlation', None) or request.POST.get('deviation', None):

            if request.POST.get('correlation', None):
                context['solution']['correlation'] = pearsonr(data_vector_exchange_rate, data_vector_index_rate)[0]
                correlation_list = list()
                correlation_list.append(context['solution']['correlation'])
                correlation_exchange_sentiment = pearsonr(data_vector_exchange_rate, data_vector_sentiment_score)[0]
                correlation_list.append(correlation_exchange_sentiment)
                correlation_index_sentiment = pearsonr(data_vector_index_rate, data_vector_sentiment_score)[0]
                correlation_list.append(correlation_index_sentiment)
                context['solution']['correlation_with_sentiment'] = np.mean(correlation_list)

            if request.POST.get('deviation', None):
                context['solution']['deviation_exchange_rate'] = np.std(data_vector_exchange_rate)
                context['solution']['deviation_index_rate'] = np.std(data_vector_index_rate)
                context['solution']['deviation_sentiment_score'] = np.std(data_vector_sentiment_score)

    return render(request, 'dashboard/index.html', context)
