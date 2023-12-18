import googlemaps

# Initialize with your Google API key
gmaps = googlemaps.Client(key='YOURGOOGLEAPIKEY')

# Geocode the address
geocode_result = gmaps.geocode(input("Please copy the address directly from XLSX file : "))
origin = geocode_result[0]['geometry']['location']

# Find nearby schools or any facility
school_types = ['school', 'university', 'college']

# Initialize an empty list to hold all places
all_places = []

# Perform a search for each type and append the results
for school_type in school_types:
    places_result = gmaps.places_nearby(location=origin, radius=5000, type=school_type)
    all_places.extend(places_result['results'])

desired_types = ["Elementary", "Middle", "High"]

# Filter the places based on desired types
filtered_places = [place for place in all_places
                   if any(desired_type in place['name'] for desired_type in desired_types)]

place_distances = []

# Calculate the distance from the address to each filtered school
for place in filtered_places:
    school_location = place['geometry']['location']
    place_name = place['name']
    distance_matrix_result = gmaps.distance_matrix(origins=[origin],
                                                   destinations=[school_location],
                                                   mode='driving')

     # Convert distance from meters to miles
    distance_meters = distance_matrix_result['rows'][0]['elements'][0]['distance']['value']
    distance_miles = distance_meters / 1609.34 
    place_distances.append((place_name, distance_miles))

# Sort the places by distance
place_distances.sort(key=lambda x: x[1])

# Print the sorted distances
for place_name, distance in place_distances:
    print(f"{place_name}: {distance:.1f} miles")