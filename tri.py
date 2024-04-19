import pandas as pd
import streamlit as st

# print(pd.DataFrame(columns=[':as','asdasd']))
data = pd.DataFrame({
        'latitude':[37.7749,34.0522,40.7128],
        'longitude':[-122.4194,-118.2437,-74.0060]
})

# Create map
st.map(data)