# Streamlit application code for the optimized XGB model to predict the UCS of cement-treated soils

import streamlit as st
import xgboost as xgb
import numpy as np
import pandas as pd
import os
import plotly.graph_objects as go

# Geting the directory of the script
script_directory = os.path.dirname(__file__)

# Loading the trained XGB model
model = xgb.XGBRegressor()
model.load_model(os.path.join(script_directory, 'newmodel.json'))

# Define the function for prediction
def predict(input_data):
    input_df = pd.DataFrame(input_data, index=[0])
    prediction = model.predict(input_df)
    return prediction[0]

# Streamlit app: Title
st.markdown("<h1 style='color: green;'>Estimation of the UCS of cement-treated soils using XGBoost model</h1>", unsafe_allow_html=True)

# Step 1: Initial condition and consistency check
st.header('Step 1: Initial conditions and consistency check')

# Input fields for parameters required to calculate n/Civ and to check the saturation 
y1, y2 = st.columns(2) # creating two column for input fields
with y1:
    ρi = st.number_input('Initial dry density of the soil (ρi) [g/cm³]', min_value=0.0, value=1.5)
    ρmax = st.number_input('Maximum dry density of the soil (ρmax) [g/cm³]', min_value=0.0, value=1.8)
    wi = st.number_input('Initial water content of the soil (wi) [%]', min_value=0.0, value=24.0)
    wopt = st.number_input('Optimum water content of the soil (wopt) [%]', min_value=0.0, value=28.0)

with y2:
    ρss = st.number_input('Specific gravity of the soil grains (ρss)', min_value=0.0, value=2.65)
    ρSC = st.number_input('Specific gravity of the cement (ρsc)', min_value=0.0, value=3.15)
    C = st.number_input('Cement dosage (%) - Range [1-10]', min_value=0.0, max_value=10.0, value=6.0)

# Calculate n and Civ using the provided equations
η = 100 - 100 * ((ρi / (1 + (C / 100))) * (1 / ρss + (C / 100) / ρSC))
Civ = (100 * ((ρi / (1 + (C / 100))) * (C / 100))) / ρSC
nCiv = η / Civ

# Saturation check and calculating the normalized dry density and water content

e = ((η/100)/(1-(η/100)))
Sat = ((wi)*ρss)/e

if Sat >= 100:
    st.write('The soil is fully saturated as Saturation exceeded 100%')
    st.stop()  # Prevent further execution if saturation exceeds 100%
else:
    st.write(f'Saturation is: **{Sat:.2f}**%')
    st.write(f'Calculated η/Civ value: **{nCiv:.2f}**')

    ρnorm = ρi/ρmax
    ωnorm = wi / wopt

    # Check if the values are out of range and notify the user
    if not (0.82 <= ρnorm <= 1.06):
     st.error(f'Input values for dry densities led to an out-of-range value for normalized dry density (ρnorm): {ρnorm:.2f}. It should be between 0.82 and 1.06.')
     st.stop()
    if not (0.32 <= ωnorm <= 1.82):
     st.error(f'Input values for water content led to an out-of-range value for normalized water content (ωnorm): {ωnorm:.2f}. It should be between 0.32 and 1.82.')
     st.stop()
    st.write(f'Calculated Normalized dry density: **{ρnorm:.2f}** [0.82, 1.06]')
    st.write(f'Calculated Normalized water content: **{ωnorm:.2f}** [0.32, 1.82]')


# Step 2: Additional parameters to estimate the UCS
st.header('Step 2: Additional parameters')

# Create two columns for inputs
col1, col2 = st.columns(2)

# Input fields for continuous features (LL, FC) in the first column
with col1:
    LL = st.number_input('Liquid Limit (%) - Range [0-60]', min_value=0.0, max_value=60.0, value=40.0)
    FC = st.number_input('Fine Contents (%) - Range [0-99]', min_value=0.0, max_value=99.0, value=30.0)
    
# Input fields for catagorical feature (Cement type) in the second column
with col2:
    cem_type = st.selectbox('Select Cement Type', ['None', 'CEM-I', 'CEM-II', 'CEM-III'])

# Initialize CEM values
CEM_I = 0
CEM_II = 0
CEM_III = 0

# Set the selected CEM type
if cem_type == 'CEM_I':
    CEM_I = 1
elif cem_type == 'CEM_II':
    CEM_II = 1
elif cem_type == 'CEM_III':
    CEM_III = 1

# Preparing base input data without curing time
base_input_data = {
    'LL': LL,
    'FC': FC,
    'CEM_I': CEM_I,
    'CEM_II': CEM_II,
    'CEM_III': CEM_III,
    'ρnorm': ρnorm,
    'ωnorm': ωnorm,
    'C': C,
    'nCiv': nCiv,
}

# UCS is to be predicted for T=7, 28, 90 days
curing_times = [7, 28, 90]

# Make predictions when the button is clicked
st.markdown("""
    <style>
    div.stButton > button {
        background-color: green;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
if st.button('Predict UCS'):
    if cem_type == 'None':
        st.write('Please select a cement type to make a prediction.')
    else:
        ucs_values = []
        for T in curing_times:
            input_data = base_input_data.copy()
            input_data['T'] = T
            prediction = predict(input_data)
            prediction = round(prediction, 1)  # Round the prediction to 1 decimal place
            ucs_values.append(prediction)
            st.write(f'The predicted UCS value at T={T} days is: **{prediction:.1f}** kPa')  # Format the output to 1 decimal place
        
        # Plotting the results
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=curing_times, 
            y=ucs_values, 
            mode='lines+markers', 
            name='',
            hovertemplate='T: %{x}<br>UCS: %{y:.1f} kPa'
        ))
        fig.update_layout(
            title='Predicted UCS vs Curing Time (T)',
            xaxis_title='Curing Time (T) [days]',
            yaxis_title='Predicted UCS [kPa]',
            template='plotly_dark'
        )
        st.plotly_chart(fig)
