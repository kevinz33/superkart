import joblib
import pandas as pd
from flask import Flask, request, jsonify

# Initialize the Flask app
superkart_api = Flask("SuperKart Sales Forecasting API")

# Load the trained sales forecasting pipeline (preprocessing + model)
model = joblib.load("superkart_model.joblib")

# Define a route for the home page
@superkart_api.get('/')
def home():
    return "Welcome to the SuperKart Sales Forecasting API!"

# Define an endpoint for online (single) inference
@superkart_api.post('/v1/predict')
def predict_sales():
    # Get JSON data from the request
    product_data = request.get_json()

    # Extract the features expected by the model
    sample = {
        "Product_Weight": product_data["Product_Weight"],
        "Product_Sugar_Content": product_data["Product_Sugar_Content"],
        "Product_Allocated_Area": product_data["Product_Allocated_Area"],
        "Product_MRP": product_data["Product_MRP"],
        "Store_Size": product_data["Store_Size"],
        "Store_Location_City_Type": product_data["Store_Location_City_Type"],
        "Store_Type": product_data["Store_Type"],
        "Product_Id_char": product_data["Product_Id_char"],
        "Store_Age_Years": product_data["Store_Age_Years"],
        "Product_Type_Category": product_data["Product_Type_Category"],
    }

    # Convert the extracted data into a single-row DataFrame
    input_data = pd.DataFrame([sample])

    # Predict the sales revenue for this product/store combination
    prediction = model.predict(input_data).tolist()[0]

    # Return the prediction as a JSON response
    return jsonify({"Predicted_Product_Store_Sales_Total": round(prediction, 2)})

# Define an endpoint for batch inference
@superkart_api.post('/v1/predictbatch')
def predict_sales_batch():
    # Get the uploaded CSV file from the request
    file = request.files['file']

    # Read the file into a DataFrame
    input_data = pd.read_csv(file)

    # Predict sales revenue for every row in the batch
    predictions = model.predict(input_data).tolist()

    # Map each row index (as a string, for valid JSON keys) to its predicted sales value
    output_dict = {str(idx): round(pred, 2) for idx, pred in enumerate(predictions)}

    return jsonify(output_dict)

# Run the Flask app
if __name__ == '__main__':
    superkart_api.run(host="0.0.0.0", port=7860, debug=True)
