from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from textblob import TextBlob
from datetime import timedelta, datetime
import json
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CorrelationPlatform.settings')
django.setup()
from dashboard.models import SentimentData, DataSource
from django.db import transaction
from django.db.models import Min

# Variables that contains the user credentials to access Twitter API
ACCESS_TOKEN = "2255998668-aFfrPqR3GLxMpzdQkG7bebh1NjfQxkt4cibwCAz"
ACCESS_TOKEN_SECRET = "HhZuKCp6m5EQg99oH3Z0kdLitD7wnVgKxQRpvS1XDH7yv"
CONSUMER_KEY = "mxTJ4ZyfuzuCZwgEH0sCmZYku"
CONSUMER_SECRET = "GgWfpDxIdQaub2QQZEVKu11ir8dGNYTyTGIflroiPJLyKftTsU"
OUTPUT_LIST = list()


# This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):
    def on_data(self, data):
        json_load = json.loads(data)
        texts = json_load['text']

        wiki = TextBlob(texts)
        r = wiki.sentiment.polarity
        OUTPUT_LIST.append(r)

        if 0 in OUTPUT_LIST:
            OUTPUT_LIST.remove(0)

        if len(OUTPUT_LIST) > 500:
            with transaction.atomic():
                for value in OUTPUT_LIST:
                    a = SentimentData()
                    a.source = DataSource.objects.get(name='sentiment_score')
                    a.value = value
                    a.save()
            del OUTPUT_LIST[:]

        min_timestamp = SentimentData.objects.all().aggregate(Min('timestamp'))['timestamp__min']
        if min_timestamp:
            min_timestamp = min_timestamp.replace(tzinfo=None)
            if datetime.utcnow() - min_timestamp > timedelta(1):
                SentimentData.objects.all().delete()


if __name__ == '__main__':
    auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    stream = Stream(auth, StdOutListener())

    stream.filter(track=['oil', 'gold', 'iron ore', 'uranium', 'reserve bank of austrialia', 'RBA', 'coal', 'AUD',
                         'Austrialian Energy'], languages=['en'], stall_warnings=True)
