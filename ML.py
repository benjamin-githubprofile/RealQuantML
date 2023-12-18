import sys
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error, r2_score
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os


def read_file(file_name):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, file_name)

    # Load the data page 1 and page 2
    data_first_sheet = pd.read_excel(file_path, sheet_name=0)


    # Concatenate the two DataFrames if they have the same structure
    data = pd.concat([data_first_sheet], ignore_index=True)

    # Drop unnecessary columns
    data = data.drop(
        ['Sold Date', 'Address', 'Website', 'Property Type'], axis=1)

    # Prepare the features and target variable
    X = data.drop('Sold Price', axis=1)
    y = data['Sold Price']

    if y.isna().any():
        print("NaNs found in target variable 'y'. Handling NaNs...")
        y = y.fillna(y.mean()) 

    imputer = SimpleImputer(strategy='mean')
    X_imputed = imputer.fit_transform(X)

    X_imputed = pd.DataFrame(X_imputed, columns=X.columns)
    # Check if there are still NaN values after imputation
    if X_imputed.isna().any().any():
        print("NaNs still exist in the features after imputation.")
    else:
        print("No NaNs in the features after imputation.")

    X_train, X_test, y_train, y_test = train_test_split(
        X_imputed, y, test_size=0.2, random_state=42)

    # Scale the features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Initialize the Linear Regression model
    model = LinearRegression()
    model_forest = RandomForestRegressor(n_estimators=100, random_state=42)

    model.fit(X_train_scaled, y_train)
    model_forest.fit(X_train_scaled, y_train)

    # Predict the target on the testing set
    y_pred = model.predict(X_test_scaled)
    y_pred_forest = model_forest.predict(X_test_scaled)

    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    mse_forest = mean_squared_error(y_test, y_pred_forest)
    r2_forest = r2_score(y_test, y_pred_forest)

    # Metrics for Linear Regression
    print(f'Mean Squared Error: {mse}')
    print(f'R-squared Score: {r2}')

    # Metrics for Random Forest
    print(f'Random Forest - Mean Squared Error: {mse_forest}')
    print(f'Random Forest - R-squared Score: {r2_forest}')

    # Coefficients
    print("\nFeature Coefficients:")
    feature_names = X.columns
    coefficients = model.coef_
    for feature, coef in zip(feature_names, coefficients):
        print(f"{feature}: {coef}")

    # Feature Importances from Random Forest
    importances = model_forest.feature_importances_
    indices = np.argsort(importances)[::-1]
    feature_names = X.columns[indices]

    # Plotting feature importances for Random Forest
    plt.figure(figsize=(10, 6))
    plt.title("Feature Importances in Random Forest")
    plt.bar(range(len(importances)), importances[indices], color="r", align="center")
    plt.xticks(range(len(importances)), feature_names, rotation=45)
    plt.xlim([-1, len(importances)])
    plt.ylabel("Importance")
    plt.xlabel("Feature")
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python real_estate_analysis.py <file_name.xlsx>")
        sys.exit(1)

    file_name = sys.argv[1]
    read_file(file_name)
