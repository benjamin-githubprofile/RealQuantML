import requests
import pandas as pd
import os
import platform
import argparse
import time


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

    response = requests.get(url, headers=headers, params=querystring)
    # Check response status
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}, {response.text}")
        return

    zillow_data = response.json()

    return zillow_data

def fetch_properties_realtor(zip_code=None, home_type=None, page=1, status_type=None, min_price=0, max_price=None):

    if status_type == "Sold":
        realtor_status_type = "sold"
    elif status_type == "ForSale":
        realtor_status_type = "ForSell"
    elif status_type == "ForRent":
        realtor_status_type = "ForRent"   
    else:
        realtor_status_type = None

    url = f"https://realtor26.p.rapidapi.com/properties/{realtor_status_type}"

    if home_type == "Single Family":
        realtor_home_type = "single-family-home"
    elif home_type == "Townhomes":
        realtor_home_type = "townhome"
    elif home_type == "Apartments":
        realtor_home_type = "condo"
    else:
        realtor_home_type = None

    if status_type:
        realtor_status_type = "sold"

    querystring = {"locationKey": zip_code,
                   "minPrice": min_price,
                   "type":[realtor_home_type] if realtor_home_type else None,
                   "maxPrice": max_price,
                   "sort":"sold-date",
                   "page": page}

    headers = {
        "X-RapidAPI-Key": "2c563d4edemsh857e6fb44733b41p11324cjsn52d715e43533",
        "X-RapidAPI-Host": "realtor26.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    realtor_data = response.json()
    return realtor_data

def fetch_and_export_data(zip_code=None, max_price=None, home_type=None, status_type=None, num_pages=None):
    # Check if max_price is provided and is a positive integer
    if max_price is None or max_price <= 0:
        print("Please enter a positive value for max price.")
        return

    # Initialize schools_data and schools_data_fetched
    schools_data = []
    zillow_properties = []
    realtor_properties = []

    for page in range(1, num_pages + 1):
        zillow_fetch = fetch_properties(zip_code, home_type, page, status_type, 0, max_price)
        if 'props' in zillow_fetch:
            zillow_properties.extend(zillow_fetch['props'])
        else:
            print(f"No data found in Zillow.com for page {page}.")
            break

        realtor_fetch = fetch_properties_realtor(zip_code, home_type, page, status_type, 0, max_price)
        if 'data' in realtor_fetch:
            realtor_properties.extend(realtor_fetch['data'])
        else:
            print(f"No data found in Realtor.com for page {page}.")
            break

        time.sleep(5)

        if page >= 3:  # Stop if max pages reached
            break
        page += 1
        print(f'Page {num_pages} fetched, moving on ...')

    if not zillow_properties:
        print("No Zillow data found for the given criteria.")
        return
    if not realtor_properties:
        print("No Realtor data found for the given criteria.")
        return

    # Convert to DataFrame
    df_props = pd.DataFrame(zillow_properties)

    if 'dateSold' in df_props.columns:
        df_props['dateSold'] = pd.to_datetime(
            df_props['dateSold'], unit="ms").dt.strftime('%m/%d/%Y')

    if 'detailUrl' in df_props.columns:
        df_props['detailUrl'] = 'https://www.zillow.com' + \
            df_props['detailUrl']

    df_props = df_props[df_props['livingArea'].notna()]

    columns_to_remove = [
        "variableData", "priceChange", "contingentListingType",
        "longitude", "latitude", "listingSubType",
        "currency", "hasImage", "newConstructionType", "lotAreaUnit", "lotAreaValue", "imgSrc"
    ]

    df_props.drop(columns=columns_to_remove, inplace=True, errors='ignore')

    new_order = [
        'dateSold', 'propertyType', 'address', 'bedrooms', 'bathrooms',
        'livingArea', 'listingStatus', 'price',
        'zestimate', 'rentZestimate', 'country', 'detailUrl', 'zpid'
    ]

    new_name_order = [
        'Sold Date', 'Property Type', 'Address', 'Number of Bedrooms',
        'Number of Bathrooms', 'Living Areas', 'Status',
        'Sold Price', 'Zestimate Price', 'Zestimate Rent Price', 'Country',
        'Website', 'Zillow ID'
    ]
    df_props = df_props[new_order]

    df_props.rename(columns=dict(zip(new_order, new_name_order)), inplace=True)
    df_props['Status'] = df_props['Status'].replace('RECENTLY_SOLD', 'SOLD')
    print("Zillow.com data successfully fetched!")
    
    df_realtor = pd.DataFrame(realtor_properties)
    print("Realtor.com data successfully fetched!")
 
    # Fetch school data only once
    first_batch = fetch_properties(
        zip_code, home_type, 1, status_type, 0, max_price)
    schools_data = first_batch.get('schools', {}).get(
        'schools', []) if first_batch else []
    df_schools = pd.DataFrame(schools_data)

    # Process school data
    columns_to_remove_schools = [ 
        "attendance_zones", "is_charter", "school_id", "location"]
    df_schools.drop(columns=columns_to_remove_schools,
                    inplace=True, errors='ignore')

    new_order_schools = ['name', 'gs_rating', 'is_elementary',
                         'is_middle', 'is_high', 'is_public', 'is_private', 'link']
    new_name_shcools = ['School Name', 'Rating', 'Elementary School?',
                        'Middle School?', 'High School?', 'Public School?',
                        'Private School?', 'Website']
    df_schools = df_schools[new_order_schools]
    df_schools.rename(columns=dict(zip(new_order_schools, new_name_shcools)), inplace=True)
    print("School data fetched!")

    # Determine the OS and set the file path
    os_type = platform.system()
    desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') if os_type == 'Windows' else os.path.join(
        os.path.join(os.path.expanduser('~')), 'Desktop')
    file_path = os.path.join(desktop_path, f"{zip_code}_{status_type}.xlsx")

    # Create a Pandas Excel writer using XlsxWriter as the engine
    writer = pd.ExcelWriter(file_path, engine='xlsxwriter')

    # Write each DataFrame to a different worksheet
    df_props.to_excel(writer, sheet_name='Zillow Properties', index=False)
    df_schools.to_excel(writer, sheet_name='Schools', index=False)
    df_realtor.to_excel(writer, sheet_name='Realtor Properties', index=False)

    writer.close()

    # Close the Pandas Excel writer and output the Excel file
    print(f"Data exported successfully to {file_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Fetch and export real estate data")
    parser.add_argument("--zip_code", type=str,
                        help="Zip code of the property location")
    parser.add_argument("--home_type", type=str, help="Single Family / Townhomes / Apartments")
    parser.add_argument("--status_type", type=str,
                        help="Status type (ForSale or ForRent or Sold)")
    parser.add_argument("--max_price", type=int,
                        help="max price (maxPrice to search)")
    parser.add_argument("--num_pages", type=int, help="Number of pages to fetch")

    args = parser.parse_args()

    fetch_and_export_data(zip_code=args.zip_code, home_type=args.home_type,
                          status_type=args.status_type, max_price=args.max_price,
                          num_pages=args.num_pages)

if __name__ == "__main__":
    main()
