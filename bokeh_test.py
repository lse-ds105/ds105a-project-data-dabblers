import os
import json
import requests
import pandas as pd
from bokeh.plotting import figure, show, output_notebook
from bokeh.models import ColumnDataSource, DatetimeTickFormatter
from bokeh.io import curdoc

# File path for the JSON data
file_path = "data/gme_daily_data.json"

# Check if the file already exists
if not os.path.exists(file_path):
    # Fetch the data only if the file does not exist
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=GME&outputsize=full&apikey=71F522PIQRFAFZZO'
    response = requests.get(url)
    gme_daily_data = response.json()

    # Save the data to a JSON file
    with open(file_path, "w") as file:
        json.dump(gme_daily_data, file)

# Reading the JSON file
gme_daily_data_df = pd.read_json('data/gme_daily_data.json')

# Extracting the relevant time series data
time_series_daily_data = gme_daily_data_df['Time Series (Daily)'].dropna().to_dict()

# Creating a new DataFrame with the structured data
gme_daily_transformed_df = pd.DataFrame.from_dict(time_series_daily_data, orient='index')
gme_daily_transformed_df.reset_index(inplace=True)
gme_daily_transformed_df.rename(columns={'index': 'Date', '1. open': 'Open', '2. high': 'High', '3. low': 'Low', '4. close': 'Close', '5. volume': 'Volume'}, inplace=True)
gme_daily_transformed_df_sorted = gme_daily_transformed_df.sort_index()

# Convert columns to appropriate data types
gme_daily_transformed_df = gme_daily_transformed_df.astype({
    'Date': 'datetime64[ns]',
    'Open': 'float',
    'High': 'float',
    'Low': 'float',
    'Close': 'float',
    'Volume': 'float'
})

# Filtering the DataFrame to include only data from December 2020 to April 2021 and creating a copy
gme_dec2020_apr2021_df = gme_daily_transformed_df[
    (gme_daily_transformed_df['Date'] >= '2020-12-01') &
    (gme_daily_transformed_df['Date'] <= '2021-04-30')
].copy()

# Set 'Date' as the DataFrame index
gme_dec2020_apr2021_df.set_index('Date', inplace=True)

# Create a ColumnDataSource for Bokeh plotting
source = ColumnDataSource(data=gme_dec2020_apr2021_df)

# Create the figure
p = figure(title="GME Daily Closing Prices (Dec 2020 - Apr 2021)", 
           x_axis_label='Date', y_axis_label='Close Price ($)', 
           x_axis_type='datetime', width=800, height=400)

# Add a line renderer with legend and line thickness
p.line(x='Date', y='Close', source=source, legend_label="Close Price", line_width=2)

# Updated format for the datetime axis
p.xaxis.formatter = DatetimeTickFormatter(
    days="%d %b %Y",
    months="%b %Y",
    years="%Y"
)

# Display the plot in the notebook
curdoc().add_root(p)
