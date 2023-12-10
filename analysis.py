import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter, MaxNLocator
import numpy as np
import sys

def millions_formatter(x, pos):
    return f'{int(x)}'

def currency_formatter(x, pos):
    return '${:,.0f}'.format(x)

# Check if the file name is provided
if len(sys.argv) < 2:
    print("Usage: python script_name.py <file_name>")
    sys.exit(1)

file_name = sys.argv[1]

data = pd.read_excel(file_name)

# Calculate statistics
mean_price = data['Sold Price'].mean()
median_price = data['Sold Price'].median()
lower_bound = data['Sold Price'].quantile(0.25)
upper_bound = data['Sold Price'].quantile(0.75)

# Date parse
data = pd.read_excel(file_name, parse_dates=['Sold Date'])
data.set_index('Sold Date', inplace=True)
data.sort_index(inplace=True)

# Define a function to remove outliers
def remove_outliers(series):
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    return series[~((series < (Q1 - 1.5 * IQR)) | (series > (Q3 + 1.5 * IQR)))]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 14))

# First subplot (original time series plot)
ax1.plot(data.index, data['Sold Price'], label='Actual Data', color='blue')
ax1.axhline(data['Sold Price'].mean(), color='red', linestyle='--', label=f'Mean: {data["Sold Price"].mean():.2f}')
ax1.axhline(data['Sold Price'].median(), color='green', linestyle='-.', label=f'Median: {data["Sold Price"].median():.2f}')
ax1.fill_between(data.index, data['Sold Price'].quantile(0.25), data['Sold Price'].quantile(0.75), color='gray', alpha=0.2, label='Interquartile Range')
ax1.xaxis.set_major_locator(mdates.MonthLocator())
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax1.yaxis.set_major_formatter(FuncFormatter(currency_formatter))
ax1.legend()
ax1.set_xlabel('Sold Date')
ax1.set_ylabel('Sold Price')
ax1.set_title('Real Estate Sold Price Analysis')
ax1.grid(True)
ax1.xaxis.set_major_locator(MaxNLocator(integer=True)) 

# Second subplot (annual average excluding outliers)
annual_data = data['Sold Price'].groupby(data.index.year).apply(remove_outliers)
annual_data = annual_data.reset_index(level=0, drop=True)  # Reset the index to remove the MultiIndex
annual_mean_prices = annual_data.groupby(annual_data.index.year).mean()
ax2.plot(annual_mean_prices.index, annual_mean_prices.values, marker='o', linestyle='-', color='green')
ax2.yaxis.set_major_formatter(FuncFormatter(currency_formatter))
ax2.set_title('Annual Average Sold Price Excluding Outliers')
ax2.set_xlabel('Year')
ax2.set_ylabel('Average Sold Price')
ax2.grid(True)
ax2.xaxis.set_major_locator(MaxNLocator(integer=True))

# Calculate and annotate the percentage change between each year
pct_changes = annual_mean_prices.pct_change().multiply(100).round(2)
for year, pct_change in pct_changes.items():
    if not np.isnan(pct_change):
        ax2.annotate(f'{pct_change:+.2f}%', 
                     xy=(year, annual_mean_prices.loc[year]), 
                     xytext=(10, 10),
                     textcoords='offset points', 
                     ha='left',  
                     va='bottom', 
                     fontweight='bold',
                     arrowprops=dict(arrowstyle='->', color='black'))

plt.tight_layout(pad=3.0)
plt.show()