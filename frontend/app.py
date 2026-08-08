import os

import pandas as pd
import requests
import streamlit as st

# The backend hostname defaults to the Docker network alias ("backend") that this
# container will be joined to; override with an env var when testing locally.
BACKEND_URL = os.environ.get("SUPERKART_BACKEND_URL", "http://backend:7860")

st.set_page_config(page_title="SuperKart Sales Forecast", page_icon="🛒")

st.title("🛒 SuperKart Sales Forecast")
st.caption(
    "Estimate the quarterly sales revenue for a product/store combination, "
    "or upload a CSV file to score many combinations at once."
)

tab_single, tab_batch = st.tabs(["Single Product Forecast", "Batch Forecast"])

with tab_single:
    with st.form("single_prediction_form"):
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Product details")
            product_weight = st.number_input("Product weight", min_value=0.0, value=12.66, step=0.1)
            product_mrp = st.number_input("Product MRP", min_value=0.0, value=117.08, step=0.5)
            product_allocated_area = st.slider(
                "Product allocated display area (share of store)", min_value=0.0, max_value=1.0, value=0.03
            )
            sugar_content = st.radio("Sugar content", ["Low Sugar", "Regular", "No Sugar"], horizontal=True)
            id_prefix = st.selectbox(
                "Product ID prefix", ["FD", "DR", "NC"], help="FD = Food, DR = Drinks, NC = Non-Consumable"
            )
            type_category = st.radio("Product type category", ["Perishables", "Non Perishables"], horizontal=True)

        with col_right:
            st.subheader("Store details")
            store_size = st.selectbox("Store size", ["Small", "Medium", "High"], index=1)
            store_city_tier = st.selectbox("Store location city type", ["Tier 1", "Tier 2", "Tier 3"], index=1)
            store_type = st.selectbox(
                "Store type",
                ["Supermarket Type1", "Supermarket Type2", "Supermarket Type3", "Departmental Store", "Food Mart"],
            )
            store_age_years = st.number_input("Store age (years)", min_value=0, value=16, step=1)

        submitted = st.form_submit_button("Forecast sales", type="primary", use_container_width=True)

    if submitted:
        request_body = {
            "Product_Weight": product_weight,
            "Product_Sugar_Content": sugar_content,
            "Product_Allocated_Area": product_allocated_area,
            "Product_MRP": product_mrp,
            "Store_Size": store_size,
            "Store_Location_City_Type": store_city_tier,
            "Store_Type": store_type,
            "Product_Id_char": id_prefix,
            "Store_Age_Years": store_age_years,
            "Product_Type_Category": type_category,
        }

        try:
            api_response = requests.post(f"{BACKEND_URL}/v1/predict", json=request_body, timeout=15)
            api_response.raise_for_status()
            forecast = api_response.json()["Predicted_Product_Store_Sales_Total"]
            st.metric("Forecasted Product_Store_Sales_Total", f"{forecast:,.2f}")
        except requests.exceptions.RequestException as exc:
            st.error(f"Could not reach the forecasting service: {exc}")
        except (KeyError, ValueError):
            st.error("The forecasting service returned an unexpected response.")

with tab_batch:
    st.subheader("Score a batch of products")
    st.write(
        "Upload a CSV containing the columns: `Product_Weight`, `Product_Sugar_Content`, "
        "`Product_Allocated_Area`, `Product_MRP`, `Store_Size`, `Store_Location_City_Type`, "
        "`Store_Type`, `Product_Id_char`, `Store_Age_Years`, `Product_Type_Category`."
    )

    uploaded_csv = st.file_uploader("Upload batch CSV", type="csv")

    if uploaded_csv is not None and st.button("Run batch forecast", type="primary"):
        try:
            api_response = requests.post(
                f"{BACKEND_URL}/v1/predictbatch",
                files={"file": (uploaded_csv.name, uploaded_csv.getvalue(), "text/csv")},
                timeout=60,
            )
            api_response.raise_for_status()

            predictions = api_response.json()
            results = pd.Series(predictions, name="Predicted_Product_Store_Sales_Total")
            results.index.name = "row"

            st.success(f"Scored {len(results)} rows.")
            st.dataframe(results, use_container_width=True)
            st.download_button(
                "Download forecasts as CSV",
                data=results.to_csv().encode("utf-8"),
                file_name="superkart_batch_forecast.csv",
                mime="text/csv",
            )
        except requests.exceptions.RequestException as exc:
            st.error(f"Could not reach the forecasting service: {exc}")
