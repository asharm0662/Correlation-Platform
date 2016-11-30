import json
from datetime import timedelta
from urllib2 import urlopen, URLError, HTTPError


def get_api_data(first_currency, second_currency, start_date, end_date):
    def date_range(start_date_range, end_date_range):
        for n in range(int((end_date_range - start_date_range).days) + 1):
            yield start_date_range + timedelta(n)

    exchange_rate_list = list()
    for single_date in date_range(start_date, end_date):
        url = "http://api.fixer.io/{0}?base={1}&symbols={1},{2}".format(str(single_date), first_currency,
                                                                        second_currency)
        try:
            response = urlopen(url)
            print "-->> Accessing " + url
            response_body = unicode(response.read(), errors="replace")
            response_to_json = json.loads(response_body)
            if 'rates' in response_to_json and 'date' in response_to_json:
                temp_dict = dict()
                temp_dict['date'] = response_to_json['date']
                if second_currency in response_to_json['rates']:
                    temp_dict['value'] = response_to_json['rates'][second_currency]
                    if temp_dict not in exchange_rate_list:
                        exchange_rate_list.append(temp_dict)

        except HTTPError, e:
            return None
        except URLError, e:
            return None

    return exchange_rate_list
