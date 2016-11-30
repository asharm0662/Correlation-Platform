import os
import json
from urllib2 import urlopen, URLError, HTTPError
from datetime import datetime, date
from csv import reader
from lxml import etree
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CorrelationPlatform.settings')
django.setup()
from dashboard.models import DataSource, DatedData
from django.db import transaction
from django.db.models import Max

DIRECTORY_NAME = os.path.join('csv')
DATE_NOW = date.today()


def download_sp():
    url = "http://chart.finance.yahoo.com/table.csv?s=%5EGSPC&d={0}&e={1}&f={2}&g=d&a=0&b=3&c=1950&ignore=.csv".format(
        int(DATE_NOW.month) - 1, DATE_NOW.day, DATE_NOW.year)
    try:
        response = urlopen(url)
        print "-->> Downloading " + url

        with open(os.path.join(DIRECTORY_NAME, '{0}.csv'.format("s&p_500")), "wb") as out_file:
            out_file.write(response.read())

    except HTTPError, e:
        print "-->> HTTP Error:", e.code, url
    except URLError, e:
        print "-->> URL Error:", e.reason, url


def csv_to_sql():
    with open(os.path.join(DIRECTORY_NAME, '{0}.csv'.format("s&p_500"))) as csv_file:
        data_source = DataSource.objects.get(name="s&p_500")
        max_date = DatedData.objects.filter(source=data_source.pk).aggregate(Max('date'))['date__max']

        csv_list = [[x[0], float(x[4])] for x in list(reader(csv_file))[1:]]

        with transaction.atomic():
            for row in csv_list:  # [slice_value:]:
                if datetime.strptime(row[0], "%Y-%m-%d").date() == max_date:
                    return
                else:
                    a = DatedData()
                    a.source = data_source
                    a.date = row[0]
                    a.value = row[1]
                    print '-->> Added    Date = {0}      Value = {1}      Source = {2}'.format(a.date, a.value,
                                                                                               a.source.name)
                    a.save()


def scrape_ftse():
    data_source = DataSource.objects.get(name="ftse_100")
    max_date = DatedData.objects.filter(source=data_source.pk).aggregate(Max('date'))['date__max']

    url = "http://markets.ft.com/data/indices/tearsheet/historical?s=FTSE:FSI"
    try:
        response = urlopen(url)
        print "-->> Accessing " + url
        response_body = unicode(response.read(), errors="replace")
        tree = etree.HTML(response_body)
        table_rows = tree.xpath('//div[@class="mod-ui-table--freeze-pane__scroll-container"]/table/tbody/tr')

        with transaction.atomic():
            for row in table_rows:
                row_date = datetime.strptime(row.xpath('.//td[1]/span/text()')[0], "%A, %B %d, %Y").date()
                row_value = row.xpath('.//td/text()')[3].replace(',', '')
                if row_date == max_date:
                    return
                else:
                    a = DatedData()
                    a.source = data_source
                    a.date = row_date
                    a.value = row_value
                    print '-->> Added    Date = {0}      Value = {1}      Source = {2}'.format(a.date, a.value,
                                                                                               a.source.name)
                    a.save()

            start_date = tree.xpath('//button[text()="Show more"]')[0].get('data-mod-results-startdate')
            url = 'http://markets.ft.com/data/equities/ajax/getmorehistoricalprices?resultsStartDate={0}&symbol=FTSE%3AFSI&isLastRowStriped=false'.format(
                start_date)

            while True:
                try:
                    response = urlopen(url)
                    print "-->> Accessing " + url
                    response_body = unicode(response.read(), errors="replace")
                    response_to_json = json.loads(response_body)['data']['html']
                    if response_to_json:
                        tree = etree.HTML(response_to_json)
                        table_rows = tree.xpath('.//tr')
                        for row in table_rows:
                            row_date = datetime.strptime(row.xpath('.//td[1]/span/text()')[0], "%A, %B %d, %Y").date()
                            row_value = row.xpath('.//td/text()')[3].replace(',', '')
                            a = DatedData()
                            a.source = data_source
                            a.date = row_date
                            a.value = row_value
                            print '-->> Added    Date = {0}      Value = {1}      Source = {2}'.format(a.date, a.value,
                                                                                                       a.source.name)
                            a.save()

                        start_date = int(start_date) - 31
                        url = 'http://markets.ft.com/data/equities/ajax/getmorehistoricalprices?resultsStartDate={0}&symbol=FTSE%3AFSI&isLastRowStriped=false'.format(
                            start_date)

                    else:
                        break

                except HTTPError, e:
                    print "-->> HTTP Error:", e.code,
                    break
                except URLError, e:
                    print "-->> URL Error:", e.reason, url
                    break

    except HTTPError, e:
        print "-->> HTTP Error:", e.code, url
    except URLError, e:
        print "-->> URL Error:", e.reason, url


if __name__ == '__main__':
    if not os.path.exists(DIRECTORY_NAME):
        os.makedirs(DIRECTORY_NAME)
    download_sp()
    csv_to_sql()
    scrape_ftse()
