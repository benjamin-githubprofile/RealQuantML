import requests
import pandas as pd
import os
import platform
import argparse


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
    if home_type is not None:
        querystring["home_type"] = home_type
    if page is not None:
        querystring["page"] = page
    if status_type is not None or status_type == "RecentlySold":
        querystring["status_type"] = status_type
        querystring["sort"] = "RecentlySold"
    if min_price is not None:
        querystring["minPrice"] = min_price

    headers = {
        "X-RapidAPI-Key": "5359e9407amsh861e763454b4f52p1000bdjsnc993ae8cee89",
        "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    # Check response status
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}, {response.text}")
        return

    data = response.json()

    return data


def fetch_and_export_data(zip_code=None, max_price=None, home_type=None, status_type=None):
    # Check if max_price is provided and is a positive integer
    if max_price is None or max_price <= 0:
        print("Please enter a positive value for max price.")
        return

    # Initialize schools_data and schools_data_fetched
    schools_data = []
    schools_data_fetched = False

    # Divide the maxPrice into four portions to create ranges
    step = max_price // 4
    price_ranges = [(0, step), (step + 1, 2 * step),
                    (2 * step + 1, 3 * step), (3 * step + 1, max_price)]

    all_properties = []

    for min_price, max_price in price_ranges:
        page = 1
        while True:
            data = fetch_properties(
                zip_code, home_type, page, status_type, min_price, max_price)
            if not data or 'props' not in data or not data['props']:
                break

            all_properties.extend(data['props'])
            if not schools_data_fetched and 'schools' in data:
                schools_data.extend(data.get('schools', {}).get('schools', []))
                schools_data_fetched = True

            if page >= data.get('totalPages', 0) or page >= 20:  # Stop if max pages reached
                break
            page += 1

    if not all_properties:
        print("No properties found for the given criteria.")
        return

    # Convert to DataFrame
    df_props = pd.DataFrame(all_properties)

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

    new_order = [
        'dateSold', 'propertyType', 'address', 'bedrooms', 'bathrooms',
        'livingArea', 'listingStatus', 'daysOnZillow', 'price',
        'zestimate', 'rentZestimate', 'country', 'detailUrl', 'zpid'
    ]

    df_props = df_props[new_order]

    df_props.drop(columns=columns_to_remove, inplace=True, errors='ignore')

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
    df_schools = df_schools[new_order_schools]

    # Determine the OS and set the file path
    os_type = platform.system()
    desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') if os_type == 'Windows' else os.path.join(
        os.path.join(os.path.expanduser('~')), 'Desktop')
    file_path = os.path.join(desktop_path, f"{zip_code}_{status_type}.xlsx")

    # Create a Pandas Excel writer using XlsxWriter as the engine
    writer = pd.ExcelWriter(file_path, engine='xlsxwriter')

    # Write each DataFrame to a different worksheet
    df_props.to_excel(writer, sheet_name='Properties', index=False)
    df_schools.to_excel(writer, sheet_name='Schools', index=False)

    # Close the Pandas Excel writer and output the Excel file
    writer.close()
    print(f"Data exported successfully to {file_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and export real estate data")
    parser.add_argument("--zip_code", type=str,
                        help="Zip code of the property location")
    parser.add_argument("--home_type", type=str, help="Type of the home")
    parser.add_argument("--status_type", type=str,
                        help="Status type (ForSale or ForRent)")
    parser.add_argument("--max_price", type=int,
                        help="max price (maxPrice to search)")

    args = parser.parse_args()

    fetch_and_export_data(zip_code=args.zip_code, home_type=args.home_type,
                          status_type=args.status_type, max_price=args.max_price)


if __name__ == "__main__":
    main()
