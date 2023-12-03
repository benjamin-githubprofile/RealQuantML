import pandas as pd
import matplotlib 
import matplotlib.dates as mdates
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import FuncFormatter, MaxNLocator
from django.shortcuts import render, HttpResponse, redirect
from .forms import UploadFileForm
import numpy as np
from io import BytesIO
import base64
import os
from django.conf import settings
from tempfile import NamedTemporaryFile

def currency_formatter(x, pos):
    return f'${x:,.0f}'

def generate_plots(data):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 14))

    # First subplot (original time series plot)
    ax1.plot(data.index, data['Sold Price'], label='Actual Data', color='blue')
    ax1.axhline(data['Sold Price'].mean(), color='red', linestyle='--', label=f'Mean: {data["Sold Price"].mean():,.2f}')
    ax1.axhline(data['Sold Price'].median(), color='green', linestyle='-.', label=f'Median: {data["Sold Price"].median():,.2f}')
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
    annual_data = annual_data.reset_index(level=0, drop=True)
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
    return fig

def remove_outliers(series):
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    return series[~((series < (Q1 - 1.5 * IQR)) | (series > (Q3 + 1.5 * IQR)))]

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the file to a temporary location
            with NamedTemporaryFile(delete=False, suffix='.xlsx', dir=settings.MEDIA_ROOT) as tmp:
                for chunk in request.FILES['file'].chunks():
                    tmp.write(chunk)
                request.session['uploaded_file_path'] = tmp.name

            data = pd.read_excel(request.FILES['file'], parse_dates=['Sold Date'])
            data.set_index('Sold Date', inplace=True)
            data.sort_index(inplace=True)

            fig = generate_plots(data)

            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            plt.close()
            graph = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return render(request, 'graphapp/graph.html', {'graph': graph})
    else:
        form = UploadFileForm()
        
    return render(request, 'graphapp/upload.html', {'form': form})


def export_pdf(request):
    file_path = request.session.get('uploaded_file_path')

    if file_path and os.path.exists(file_path):
        # Read the data from the saved file
        data = pd.read_excel(file_path, parse_dates=['Sold Date'])
        data.set_index('Sold Date', inplace=True)
        data.sort_index(inplace=True)

        fig = generate_plots(data)

        pdf_buffer = BytesIO()
        with PdfPages(pdf_buffer) as pdf:
            pdf.savefig(fig)
        pdf_buffer.seek(0)

        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="exported_graphs.pdf"'
        return response

    return redirect('upload_file')