import os
import json
import requests
import pandas as pd
from bokeh.plotting import figure, show, output_file, save, curdoc
from bokeh.models import ColumnDataSource, LinearColorMapper, ColorBar, NumeralTickFormatter, Title
from bokeh.transform import transform
from bokeh.models.widgets import Slider 
from bokeh.models.callbacks import CustomJS
from bokeh.models import Range1d
import pandas as pd
from bokeh.layouts import column
from bokeh.models import LinearAxis
from bokeh.models import HoverTool

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
    'Volume': 'int'
})

# Filtering the DataFrame to include only data from December 2020 to April 2021 and creating a copy
gme_jan_apr2021_df = gme_daily_transformed_df[(gme_daily_transformed_df['Date'] >= '2021-01-01') & (gme_daily_transformed_df['Date'] <= '2021-04-01')].copy()
# Set 'Date' as the DataFrame index
gme_jan_apr2021_df.set_index('Date', inplace=True)

df_data1 = pd.read_csv('./data/reddit_data/Submissions_2021-01_FilteredBySubreddit_GME.csv')
df_data2 = pd.read_csv('./data/reddit_data/Submissions_2021-02_FilteredBySubreddit_GME.csv')
df_data3 = pd.read_csv('./data/reddit_data/Submissions_2021-03_FilteredBySubreddit_GME.csv')

df_all_data = pd.concat([df_data1, df_data2, df_data3], axis = 0,
                        ignore_index=True)

# Remove curly brackets from num_comments and score columns
df_all_data['num_comments'] = df_all_data['num_comments'].str.replace('[{}]'.format(''.join(['{}'])), '', regex=True)
df_all_data['score'] = df_all_data['score'].str.replace('[{}]'.format(''.join(['{}'])), '', regex=True)


# Remove date and time from num_comments and score columns
df_all_data['num_comments'] = df_all_data['num_comments'].str.split(':').str[-1].str.strip()
df_all_data['score'] = df_all_data['score'].str.split(':').str[-1].str.strip()


# Convert num_comments and score columns to integers
df_all_data['num_comments'] = df_all_data['num_comments'].astype(int)
df_all_data['score'] = df_all_data['score'].astype(int)


df_all_data['created_at'] = pd.to_datetime(df_all_data['created_at'])
# Extract only the date part
df_all_data['created_at'] = df_all_data['created_at'].dt.normalize()

df_all_data.rename(columns={'created_at': 'Date'}, inplace=True)
df_grouped = df_all_data.groupby('Date')

df_grouped = df_all_data.groupby('Date').size().reset_index(name='Post_Count')

df_comments_count = df_all_data.groupby('Date')['num_comments'].sum().reset_index(name='Total_Comments')

# Merge 'df_grouped' with 'df_comments_count' on 'Date'
df_grouped = df_grouped.merge(df_comments_count, on='Date', how='left')

merged_df = df_grouped.merge(gme_jan_apr2021_df, on='Date', how='outer')
cleaned_df = merged_df.dropna()
#cleaned_df['Volume'] = cleaned_df['Volume'].astype(int)
# Remove the last row using .iloc
cleaned_df = cleaned_df.iloc[:-1, :]



# Ensure your dataframe is sorted by date if it's not already
cleaned_df['Date'] = pd.to_datetime(cleaned_df['Date'])
cleaned_df.sort_values('Date', inplace=True)

# Add a visibility column to your DataFrame
cleaned_df['visible'] = False

# Create a ColumnDataSource from the dataframe
source = ColumnDataSource(cleaned_df)

# Create a color mapper for total comments with a color bar
color_mapper = LinearColorMapper(palette="Viridis256", low=cleaned_df['Total_Comments'].min(), high=cleaned_df['Total_Comments'].max())

# Define a size mapping and update the source
scale_factor = 0.0015
max_size = 10000
min_size = 5
cleaned_df['size'] = cleaned_df['Post_Count'] * scale_factor
cleaned_df['size'] = cleaned_df['size'].clip(lower=min_size, upper=max_size)

# Update the source with the new size data
source.data['size'] = cleaned_df['size']

# Create a figure object
p = figure(width=1450, height=700, x_axis_type="datetime")
p.title = Title(text="WSB Activity vs GME Trading Volume", text_font_size="20pt", align="center")

# Add circle glyphs to the figure
circle_glyph = p.circle(x='Date', y='Volume', size='size', source=source, color=transform('Total_Comments', color_mapper), alpha=0.7, legend_label='Total Comments', muted_alpha=0.2)
p.legend.click_policy = 'mute'

# Add a color bar to the right of the plot
color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12, location=(0, 0), title='Total Comments', formatter=NumeralTickFormatter(format="0,0"))
p.add_layout(color_bar, 'below')

# Customize the plot
p.yaxis.formatter = NumeralTickFormatter(format="0a")
p.xaxis.axis_label = 'Date'
p.yaxis.axis_label = 'Trading Volume (in millions)'


# Specify the range for the secondary y-axis (right side)
p.extra_y_ranges = {'Close Price': Range1d(start=cleaned_df['Close'].min(), end=cleaned_df['Close'].max())}


# Add the secondary y-axis (right side) for Close Price
p.line('Date', 'Close', source=source, color='red', y_range_name='Close Price', legend_label='Close Price')
p.add_layout(LinearAxis(y_range_name='Close Price', axis_label='Close Price'), 'right')

# Add hover tool
hover = HoverTool(tooltips=[("Date", "@Date{%F}"),
                            ("Volume", "@Volume"),
                            ("Post Count", "@Post_Count"),
                            ("Total Comments", "@Total_Comments"),
                            ("Close Price", "@Close")],
                  formatters={'@Date': 'datetime'})
p.add_tools(hover)

slider = Slider(start=0, end=len(source.data['Date']), step=1, value=0, title="Animate Circles")
slider.js_on_change("value", CustomJS(args=dict(source=source, slider=slider), code="""
    const dataLength = source.data['Date'].length;
    const end = slider.value;
    for (let i = 0; i < dataLength; i++) {
        source.data['visible'][i] = i < end;
    }
    source.change.emit();
"""))
# Create a layout for the plot and slider
layout = column(p, slider)

# Show the plot
curdoc().add_root(layout)
output_file("animated_plot.html")
save(layout)


# Run the server
# To run this, you would save it as a .py file and then run `bokeh serve --show mydashboard.py`
