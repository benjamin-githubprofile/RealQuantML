import requests
import pandas as pd
import os
import platform
import argparse
import time
from datetime import datetime

# funciton to fetch Zillow data


def fetch_properties(zip_code=None, home_type=None, page=1, status_type=None, min_price=None, max_price=None):
    url = "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch"

    querystring = {}

    # Check for zip_code validity
    if zip_code is None:
        print("No Zipcode Provided, please enter Zipcode: ")
        return
    elif len(zip_code) != 5 or not zip_code.isdigit():
        print("Zipcode is incorrect, please enter a valid 5 digits zipcode")
        return
    else:
        querystring["location"] = zip_code
        querystring["schools"] = "elementary,middle,high"

    if max_price is not None:
        if not str(max_price).isdigit() or max_price == "":
            print("Please re-enter a valid amount, no symbols needed for price")
            return
        else:
            querystring["maxPrice"] = max_price

    # Add other parameters if zip_code provided
    if home_type is not None and home_type == "Single Family":
        querystring["home_type"] = "Houses"
    elif home_type is not None and home_type == "Townhomes" or home_type == "Apartments":
        querystring["home_type"] = home_type
    if page is not None:
        querystring["page"] = page
    if status_type is not None and status_type == "Sold":
        querystring["status_type"] = "RecentlySold"
        querystring["sort"] = "RecentlySold"
    if min_price is not None:
        querystring["minPrice"] = min_price

    headers = {
        "X-RapidAPI-Key": "2c563d4edemsh857e6fb44733b41p11324cjsn52d715e43533",
        "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com"
    }
    # print(f"Requesting Zillow URL: {url} with params: {querystring}")
    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}, {response.text}")
        return
    zillow_data = response.json()
    return zillow_data

# funciton to fetch Realtor data


def fetch_properties_realtor(zip_code=None, home_type=None, page=1, status_type=None, min_price=0, max_price=None):

    if status_type == "Sold":
        realtor_status_type = "sold"
        sort_option = "sold-date"
    elif status_type == "ForSale":
        realtor_status_type = "buy"
        sort_option = "newest"
    elif status_type == "ForRent":
        realtor_status_type = "rent"
        sort_option = "recently-added"
    else:
        realtor_status_type = None
        sort_option = None

    url = f"https://realtor26.p.rapidapi.com/properties/{realtor_status_type}"

    if home_type == "Single Family":
        realtor_home_type = "single-family-home"
    elif home_type == "Townhomes":
        realtor_home_type = "townhome"
    elif home_type == "Apartments":
        realtor_home_type = "condo"
    else:
        realtor_home_type = None

    querystring = {"locationKey": zip_code,
                   "minPrice": min_price,
                   "type": [realtor_home_type] if realtor_home_type else None,
                   "maxPrice": max_price,
                   "sort": sort_option,
                   "page": page}

    headers = {
        "X-RapidAPI-Key": "2c563d4edemsh857e6fb44733b41p11324cjsn52d715e43533",
        "X-RapidAPI-Host": "realtor26.p.rapidapi.com"
    }
    # print(f"Requesting Realtor URL: {url} with params: {querystring}")
    response = requests.get(url, headers=headers, params=querystring)
    realtor_data = response.json()
    return realtor_data

# funciton to export data


def fetch_and_export_data(zip_code=None, max_price=None, home_type=None, status_type=None, num_pages=None):
    # Check if max_price is provided and is a positive integer
    if max_price is None or max_price <= 0:
        print("Please enter a positive value for max price.")
        return

# list to store data
    schools_data = []
    zillow_properties = []
    realtor_properties = []

# roll both data from page 1 to page num_pages
    for page in range(1, num_pages + 1):
        zillow_fetch = fetch_properties(
            zip_code, home_type, page, status_type, 0, max_price)
        if 'props' in zillow_fetch:
            zillow_properties.extend(zillow_fetch['props'])
            time.sleep(6)
        else:
            print(f"No data found in Zillow.com for page {page}.")
            break

        realtor_fetch = fetch_properties_realtor(
            zip_code, home_type, page, status_type, 0, max_price)
        if 'data' in realtor_fetch:
            realtor_properties.extend(realtor_fetch['data'])
            time.sleep(6)
        else:
            print(f"No data found in Realtor.com for page {page}.")
            break

        # add time.sleep to prevent API rate limit
        time.sleep(5)
        print(f'Page {page} fetched, moving on ...')
        if page >= 20:
            break
        time.sleep(5)

    if not zillow_properties:
        print("No Zillow data found for the given criteria.")
        return
    if not realtor_properties:
        print("No Realtor data found for the given criteria.")
        return

# setup dataframe(excel) for Zillow
    df_props = pd.DataFrame(zillow_properties)

    # step 1 cleanup: remove NaN value
    df_props.dropna(subset=['livingArea'], inplace=True)
    df_props.dropna(subset=['price'], inplace=True)
    for column in ['bedrooms', 'bathrooms']:
        if column in df_props.columns:
            df_props[column].ffill(inplace=True)

    # reformat url for better visualization
    if 'detailUrl' in df_props.columns:
        df_props['detailUrl'] = 'https://www.zillow.com' + \
            df_props['detailUrl']

    # remove unwanted columns in different conditions and rename
    if status_type in ["ForSale", "ForRent"]:
        columns_to_remove = [
            "variableData", "priceChange", "contingentListingType",
            "longitude", "latitude", "zpid", "listingSubType",
            "currency", "hasImage", "newConstructionType", "lotAreaUnit", "lotAreaValue", "imgSrc", 'listingStatus', 'country'
        ]

        df_props.drop(columns=columns_to_remove, inplace=True, errors='ignore')

        new_order = [
            'dateSold', 'address', 'price', 'zestimate', 'rentZestimate', 'detailUrl',
            'bedrooms', 'bathrooms', 'livingArea', 'propertyType', 'daysOnZillow'
        ]
        new_name_order = [
            'Sold Date', 'Address', 'Listed Price', 'Zestimate Price', 'Zestimate Rent Price',
            'Website', 'Bedrooms', 'Bathrooms', 'Living Area', 'Property Type', 'Time On Market'
        ]

        df_props = df_props[new_order]
        df_props.rename(columns=dict(
            zip(new_order, new_name_order)), inplace=True)

    else:
        columns_to_remove = [
            "variableData", "priceChange", "contingentListingType",
            "longitude", "latitude", "listingSubType",
            "currency", "hasImage", "newConstructionType", "lotAreaUnit", "lotAreaValue", "imgSrc",
            'zpid', 'listingStatus', 'country', 'zestimate', 'rentZestimate'
        ]

        df_props.drop(columns=columns_to_remove, inplace=True, errors='ignore')

        if 'dateSold' in df_props.columns:
            df_props['dateSold'] = pd.to_datetime(
                df_props['dateSold'].astype(int), unit='ms', errors='coerce')
            df_props.dropna(subset=['dateSold'], inplace=True)
            df_props['dateSold'] = df_props['dateSold'].dt.strftime('%m/%d/%Y')

        new_order = [
            'dateSold', 'address', 'price', 'detailUrl',
            'bedrooms', 'bathrooms', 'livingArea', 'propertyType', 'daysOnZillow'
        ]
        new_name_order = [
            'Sold Date', 'Address', 'Sold Price', 'Website',
            'Bedrooms', 'Bathrooms', 'Living Area', 'Property Type', 'Time On Market'
        ]

        df_props = df_props[new_order]
        df_props.rename(columns=dict(
            zip(new_order, new_name_order)), inplace=True)
    print("Zillow.com and Realtor.com successfully fetched!")
    time.sleep(5)

    # realtor API
    df_realtor = pd.DataFrame(realtor_properties)

    def format_address(location):
        address = location.get('address', '')
        city = location.get('city', '')
        state = location.get('state', '')
        postal_code = location.get('postalCode', '')

        formatted_address = f"{address}, {city}, {state} {postal_code}"
        return formatted_address

    # format address
    df_realtor['formatted_address'] = df_realtor['location'].apply(
        format_address)

    # Preprocess the date columns
    df_realtor['listDate'] = pd.to_datetime(
        df_realtor['listDate'], format='%Y-%m-%dT%H:%M:%S.%fZ', utc=True)
    df_realtor['listDate'] = df_realtor['listDate'].dt.strftime('%m/%d/%Y')
    df_realtor['soldDate'] = pd.to_datetime(
        df_realtor['soldDate'], format='%Y-%m-%d')

    # calculate days on market
    if status_type in ["ForSale", "ForRent"]:
        df_realtor['listDate'] = pd.to_datetime(
            df_realtor['listDate'], format='%m/%d/%Y', errors='coerce', utc=True)
        df_realtor['listDate'] = df_realtor['listDate'].dt.tz_localize(None)
        df_realtor['Time On Market'] = (
            datetime.now() - df_realtor['listDate']).dt.days
    else:
        df_realtor['soldDate'] = pd.to_datetime(
            df_realtor['soldDate'], errors='coerce')
        df_realtor['listDate'] = pd.to_datetime(
            df_realtor['listDate'], errors='coerce', utc=True)
        df_realtor['listDate'] = df_realtor['listDate'].dt.tz_localize(None)
        df_realtor['Time On Market'] = (
            df_realtor['soldDate'] - df_realtor['listDate']).dt.days
        df_realtor['soldDates'] = df_realtor['soldDate'].dt.strftime(
            '%m/%d/%Y')

    # remove columns in different conditions and rename
    if status_type in ["ForSale", "ForRent"]:
        realtor_columns_to_remove = [
            "propertyId", "listingId", "priceMin", "priceMax", "permalink", "soldPrice", "soldDate", "listDate"
        ]
        new_realtor_order = [
            'formatted_address', 'price', 'Time On Market', 'url'
        ]
        new_realtor_name_order = [
            "Address", "Listed Price", 'Time On Market', "Website"
        ]

    else:
        realtor_columns_to_remove = [
            'propertyId', 'listingId', 'priceMin', 'priceMax', 'permalink', 'location'
        ]
        new_realtor_order = [
            'soldDates', 'formatted_address', 'price', 'url', 'Time On Market'
        ]
        new_realtor_name_order = [
            'Sold Date', 'Address', 'Sold Price', 'Website', 'Time On Market'
        ]
    df_realtor.drop(columns=realtor_columns_to_remove,
                    inplace=True, errors='ignore')
    df_realtor = df_realtor[new_realtor_order]
    df_realtor.rename(columns=dict(
        zip(new_realtor_order, new_realtor_name_order)), inplace=True)
    print("realtor columns: ", df_realtor.columns)

    time.sleep(5)

    # Fetch school data
    first_batch = fetch_properties(
        zip_code, home_type, 1, status_type, 0, max_price)
    schools_data = first_batch.get('schools', {}).get(
        'schools', []) if first_batch else []
    df_schools = pd.DataFrame(schools_data)
    columns_to_remove_schools = [
        "attendance_zones", "is_charter", "school_id", "location"]
    df_schools.drop(columns=columns_to_remove_schools,
                    inplace=True, errors='ignore')
    new_order_schools = ['name', 'gs_rating', 'is_elementary',
                         'is_middle', 'is_high', 'is_public', 'is_private', 'link']
    new_name_shcools = ['School Name', 'Rating', 'Elementary School?',
                        'Middle School?', 'High School?', 'Public School?',
                        'Private School?', 'School Website']
    df_schools = df_schools[new_order_schools]
    df_schools.rename(columns=dict(
        zip(new_order_schools, new_name_shcools)), inplace=True)

    print("School data fetched!")
    time.sleep(5)

    # os file path
    os_type = platform.system()
    desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') if os_type == 'Windows' else os.path.join(
        os.path.join(os.path.expanduser('~')), 'Desktop')
    file_path = os.path.join(
        desktop_path, f"{zip_code}_{status_type}_{home_type}.xlsx")

    # XlsxWriter as the engine
    writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
    df_combined_old = pd.concat([df_props, df_realtor]).reset_index(drop=True)
    # print(f"df_combined_old DataFrame shape: {df_combined_old.shape}")

    # drop duplicate
    df_combined_old.drop_duplicates(
        subset='Address', keep='first', inplace=True)
    if status_type not in ["ForSale", "ForRent"]:
        new_combined_order = ['Sold Date', 'Address', 'Sold Price',
                              'Bedrooms', 'Bathrooms', 'Living Area',
                              'Property Type', 'Time On Market', 'Website']
    else:
        new_combined_order = ['Address', 'Listed Price',
                              'Bedrooms', 'Bathrooms', 'Living Area',
                              'Property Type', 'Time On Market', 'Website']
    df_combined = df_combined_old[new_combined_order].copy()

    # format date
    if status_type not in ["ForSale", "ForRent"]:
        df_combined['Sold Date'] = pd.to_datetime(df_combined['Sold Date'])
        df_combined = df_combined.sort_values(by='Sold Date', ascending=False)
        df_combined['Sold Date'] = df_combined['Sold Date'].dt.strftime(
            '%m/%d/%Y')

    if status_type not in ["ForSale", "ForRent"]:
        # Format numeric values and handle NaN
        df_combined['Sold Price'] = pd.to_numeric(
            df_combined['Sold Price'], errors='coerce')
        df_combined['Sold Price'].ffill(inplace=True)
        df_combined['Bedrooms'] = pd.to_numeric(
            df_combined['Bedrooms'], errors='coerce')
        df_combined['Bathrooms'] = pd.to_numeric(
            df_combined['Bathrooms'], errors='coerce')
        df_combined['Living Area'] = pd.to_numeric(
            df_combined['Living Area'], errors='coerce')
    else:
        df_combined['Listed Price'] = pd.to_numeric(
            df_combined['Listed Price'], errors='coerce')
        df_combined['Listed Price'].ffill(inplace=True)
        df_combined['Bedrooms'] = pd.to_numeric(
            df_combined['Bedrooms'], errors='coerce')
        df_combined['Bathrooms'] = pd.to_numeric(
            df_combined['Bathrooms'], errors='coerce')
        df_combined['Living Area'] = pd.to_numeric(
            df_combined['Living Area'], errors='coerce')

    # Fill NaN values for numeric columns
    for column in ['Bedrooms', 'Bathrooms', 'Living Area']:
        df_combined[column].fillna(df_combined[column].median(), inplace=True)

    # handle NaN value for 'Property Type'
    df_combined['Property Type'] = home_type

    # if status is ForSale or ForRent, filter out '0' Listed Price
    if status_type in ["ForSale", "ForRent"]:
        df_combined = df_combined[df_combined['Listed Price'] != 0]

    # int days on market and absolute value
    df_combined['Time On Market'] = df_combined['Time On Market'].astype(int)
    df_combined['Time On Market'] = df_combined['Time On Market'].abs()

    # sort date from newest to oldest
    if status_type in ["ForSale" or "ForRent"]:
        df_combined.sort_values(by='Time On Market',
                                ascending=False, inplace=True)

    # export to excel
    df_combined.to_excel(writer, sheet_name='Combined Properties', index=False)
    df_schools.to_excel(writer, sheet_name='Schools', index=False)
    writer.close()
    print(f"Data exported successfully to {file_path} ... Program End")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and export real estate data")
    parser.add_argument("--zip_code", type=str,
                        help="Zip code of the property location")
    parser.add_argument("--home_type", type=str,
                        help="Single Family / Townhomes / Apartments")
    parser.add_argument("--status_type", type=str,
                        help="Status type (ForSale or ForRent or Sold)")
    parser.add_argument("--max_price", type=int,
                        help="max price (maxPrice to search)")
    parser.add_argument("--num_pages", type=int,
                        help="Number of pages to fetch")

    args = parser.parse_args()

    fetch_and_export_data(zip_code=args.zip_code, home_type=args.home_type,
                          status_type=args.status_type, max_price=args.max_price,
                          num_pages=args.num_pages)


if __name__ == "__main__":
    main()
