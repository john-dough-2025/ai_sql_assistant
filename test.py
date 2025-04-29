import streamlit as st
import pandas as pd

# Data for top 10 customers
customers = {
    "Customer#000694366": 7157578.07,
    "Customer#000317698": 7074577.74,
    "Customer#000750415": 6960493.18,
    "Customer#000359587": 6930237.45,
    "Customer#000910705": 6923991.73,
    "Customer#000571483": 6914311.46,
    "Customer#000135679": 6874546.75,
    "Customer#000998602": 6868616.10,
    "Customer#000022999": 6828807.77,
    "Customer#000084427": 6810146.87
}

# Convert to DataFrame
df = pd.DataFrame(list(customers.items()), columns=['Customer', 'Total Purchases'])

# Render a bar chart
code = "st.bar_chart(df.set_index('Customer'))"

exec(code)