from flask import Flask, render_template, request, redirect
import requests
import simplejson as json
import pandas as pd
from pandas import DataFrame
from bokeh.plotting import figure
from bokeh.embed import components
import numpy as np

app = Flask(__name__)
app.vars= {}

#set api key and link - TODO: change to collect this from config file
QUANDL_BASE_URL = 'https://www.quandl.com/api/v3/datatables/WIKI/PRICES.json?'
API_KEY = 'xFNtCxoxc8BksE1MXfk1'
col_options = ['open','close','high','low']
graph_line_colors = ['maroon','navy','gray','green']

#set initial values
app.vars['ticker'] = 'AAPL'
app.vars['columns'] = 'close'
app.vars['start'] = '2011-01-01'
app.vars['end'] = '2017-01-01'
app.vars['open'] = ''
app.vars['close'] = 'checked'
app.vars['high'] = ''
app.vars['low'] = ''

@app.route('/')
def main():
    #generate initial graph
    script, div = generate_graph()
    return render_template('index.html', graph_div = div, script=script, 
              ticker=app.vars['ticker'], start=app.vars['start'], end=app.vars['end'],
              open=app.vars['open'], close=app.vars['close'], high=app.vars['high'], low=app.vars['low'])

def retrieve_page(params):
    quandl_url = QUANDL_BASE_URL + params + '&api_key=' + API_KEY
    response = requests.get(quandl_url)

    if response.status_code != 200:
        print ("Cannot fetch data {} from Quandl. \nStatus code: {}, Reason: {}"
            .format(params, response.status_code, response.reason))
    return response

def generate_graph():
    # set params for quandl API call
    ticker=app.vars['ticker']
    columns=app.vars['columns']+',date'
    start=app.vars['start']
    end=app.vars['end']
    params = 'ticker='+ticker+'&qopts.columns='+columns+'&date.gte='+start+'&date.lte='+end
    # make api call
    quandl_response = retrieve_page(params)

    # store data in dataframe
    data_json = json.loads(quandl_response.text)
    data_cols = [x['name'] for x in data_json['datatable']['columns']]
    data = DataFrame(data_json['datatable']['data'], columns = data_cols)

    # extract values for bokeh graph
    dates = np.array(data['date'],dtype=np.datetime64)

    # window_size = 30
    # window = np.ones(window_size)/float(window_size)

    p = figure(width=800, height=350, x_axis_type="datetime")

    for i, col in enumerate(data.columns[data.columns.isin(col_options)]):
        p.line(dates, data[col].tolist(), color=graph_line_colors[i],legend=col)
    
    p.title.text = '{} Prices: {} to {}'.format(ticker, start, end)
    p.legend.location = "top_left"
    p.grid.grid_line_alpha=0
    p.xaxis.axis_label = 'Date'
    p.yaxis.axis_label = 'Price'
    p.ygrid.band_fill_color="skyblue"
    p.ygrid.band_fill_alpha = 0.1

    return components(p)




@app.route('/index',methods=['GET','POST'])
def index():
    # save form values
    app.vars['ticker'] = request.form['ticker']
    columns = []
    for col in col_options:
        if request.form.get(col) == 'on':
            columns.append(col)
            app.vars[col] = 'checked'
        else:
            app.vars[col] = ''
    
    app.vars['columns'] = ','.join(columns)
    app.vars['start'] = request.form['start']
    app.vars['end'] = request.form['end']
    
    script, div = generate_graph()
    return render_template('index.html',graph_div = div, script=script, 
              ticker=app.vars['ticker'], start=app.vars['start'], end=app.vars['end'],
              open=app.vars['open'], close=app.vars['close'], high=app.vars['high'], low=app.vars['low'])

if __name__ == '__main__':
  app.run(port=33507, debug=True)
