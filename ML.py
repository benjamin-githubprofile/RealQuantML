import sys
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import os


def read_file(file_name):
    # Construct the file path assuming the file is in the same directory as the script
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, file_name)

    # Load the data
    data_first_sheet = pd.read_excel(file_path, sheet_name=0)

    # Load the data from the second sheet
    data_second_sheet = pd.read_excel(file_path, sheet_name=1)

    # Replace 'TRUE' with 0 and 'FALSE' with 1 in the second sheet
    data_second_sheet.replace({'TRUE': 0, 'FALSE': 1}, inplace=True)

    # Concatenate the two DataFrames if they have the same structure
    data = pd.concat([data_first_sheet, data_second_sheet], ignore_index=True)

    # Drop unnecessary columns
    data = data.drop(
        ['Sold Date', 'Address', 'Website', 'Property Type', 'School Website', 'School Name'], axis=1)

    # Prepare the features and target variable
    X = data.drop('Sold Price', axis=1)
    y = data['Sold Price']

    # Split the dataset into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    # Scale the features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Initialize the Linear Regression model
    model = LinearRegression()

    # Train the model
    model.fit(X_train_scaled, y_train)

    # Predict the target on the testing set
    y_pred = model.predict(X_test_scaled)

    # Evaluate the model performance
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Print evaluation metrics
    print(f'Mean Squared Error: {mse}')
    print(f'R-squared Score: {r2}')

    # Print the coefficients of each feature
    print("\nFeature Coefficients:")
    feature_names = X.columns
    coefficients = model.coef_
    for feature, coef in zip(feature_names, coefficients):
        print(f"{feature}: {coef}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python real_estate_analysis.py <file_name.xlsx>")
        sys.exit(1)

    file_name = sys.argv[1]
    read_file(file_name)
