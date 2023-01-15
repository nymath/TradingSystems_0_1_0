from datetime import datetime 
import json
import pandas as pd
import requests

ALPHA_VANTAGE_BASE_URL = 'https://www.alphavantage.co'
ALPHA_VANTAGE_TIME_SERIES_CALL = 'query?function=TIME_SERIES_DAILY_ADJUSTED'
COLUMNS = ['Date', 'Open', 'High', 'Low', 'Close', 'Volumn', 'Adj Close']

class AlphaVantage(object):
    """
    Encapsulates calls to the AlphaVantage API with a provided API key.
    """
    
    def __init__(self, api_key='UZ5X9CE8M6R4ASOE'):
        
        self.api_key = api_key
        
    def _construct_alpha_vantage_symbol_call(self, ticker):
        return "%s/%s&symbol=%s&outputsize=full&apikey=%s" % (
        ALPHA_VANTAGE_BASE_URL, 
        ALPHA_VANTAGE_TIME_SERIES_CALL, 
        ticker, 
        self.api_key
        )

    def get_daily_historic_data(self, ticker, start_date, end_date):
        av_url = self._construct_alpha_vantage_symbol_call(ticker)
        
        try:
            av_data_js = requests.get(av_url) 
            data = json.loads(av_data_js.text)['Time Series (Daily)']
        except Exception as e:
            print("Could not download AlphaVantage data for %s ticker " "(%s)...stopping." % (ticker, e)) 
            return pd.DataFrame(columns=COLUMNS).set_index('Date')
        else:
            prices = [] 
            for date_str in sorted(data.keys()):
                date = datetime.strptime(date_str, '%Y-%m-%d') 
                if date < start_date or date > end_date:
                    continue
                bar = data[date_str] 
                prices.append((
                    date, 
                    float(bar['1. open']), 
                    float(bar['2. high']), 
                    float(bar['3. low']), 
                    float(bar['4. close']), 
                    int(bar['6. volume']),
                    float(bar['5. adjusted close'])
                ))
        return pd.DataFrame(prices, columns=COLUMNS).set_index('Date')