# REFERENCES
# https://deckgl.readthedocs.io/en/latest/gallery/globe_view.html
# https://deck.gl/docs/
# https://python.plainenglish.io/building-lightweight-geospatial-data-viewers-with-streamlit-and-pydeck-de1e0fbd7ba7
# https://stackoverflow.com/questions/33158417/pandas-combine-two-strings-ignore-nan-values
# https://blog.streamlit.io/auto-generate-a-dataframe-filtering-ui-in-streamlit-with-filter_dataframe/

import pandas as pd
import streamlit as st
import pydeck as pdk
import random
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)

UPDATE_COLOURS = False

st.set_page_config(
    layout="wide",
    page_title="Mapping ProMED Alerts",
    page_icon='🌏')

st.header("Mapping disease instances from ProMED alerts")

intro = "The [Program for Monitoring Emerging Diseases (ProMED)](https://promedmail.org/about-promed/) is a program of the International Society for Infectious Diseases (ISID). ProMED was launched in 1994 as an Internet service to identify unusual health events related to emerging and re-emerging infectious diseases and toxins affecting humans, animals and plants. It is the largest publicly-available system conducting global reporting of infectious disease outbreaks. "
st.write(intro)
st.write("\n\n")
st.text("Hover over a point to view more information. You can also filter on countries, pathogen type, disease name, and affected species")

def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Filter data")

    if not modify:
        return df

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", ['Country','Disease name','Pathogen type','Affected species'])#df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            left.write("↳")
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].sort_values().unique(),
                    default=[]#list(df[column].sort_values().unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    _min,
                    _max,
                    (_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].str.contains(user_text_input)]

    return df


@st.cache_data()
def getDiseaseData(path):
    return pd.read_excel(path)

@st.cache_data()
def getColourData(path):
    return pd.read_excel(path).drop(columns="Unnamed: 0")

def getRandomColour():
    R = random.randrange(10,256)
    G = random.randrange(10,256)
    B = random.randrange(10,256)
    return [R,G,B]
    

# Set height and width variables
view = pdk.View(type="_GlobeView", controller=True, width=1000, height=700)

colourDict = dict()

# Get disease data from Excel file
data = getDiseaseData("tracker.xlsx")

# Get the colours for each disease
currentDiseaseColours = getColourData("colours.xlsx")

# Conver the dataframe into a dictionary to ease access
colourDict = {row[1]['Disease']:eval(row[1]['Colour']) for row in currentDiseaseColours.iterrows()}

diseases = data['Disease name'].unique()

colourList = list()
# print(currentDiseaseColours)
for i in data['Disease name'].values:
    if i in colourDict:
        # colourList will be added as an extra column to disease data
        colourList.append(colourDict[i])
    else:
        newColour = getRandomColour()
        # To ensure newColour is unique
        while newColour in colourDict.values():
            newColour = getRandomColour()
        colourList.append(newColour)
        colourDict[i] = newColour
        # print([i,newColour])

        # Updating the existing colour df to include the previously unseen disease
        currentDiseaseColours.loc[len(currentDiseaseColours)] = [i,newColour]

# Updating the disease colours Excel file
if UPDATE_COLOURS:
    currentDiseaseColours.to_excel('colours.xlsx')

# For displaying the location in the map, we add a new column which is the concatenation of region, state and country
# Missing fields are ignored. i.e. if a particular row does not have a specified state, it will print "{region}, {country}"
# instead of "{region}, NaN, {country}"
cols =['Region','State','Country']
data['Place'] = data[cols].apply(lambda x:x.str.cat(sep=', '),axis=1)

# We convert all columns to Categorical so filtering the dataframe is easier with the filter_dataframe function.
# It also has the added benefit of reducing the size of the variable.
data = data.astype('category')
data['color'] = colourList
df = filter_dataframe(data)

layers = [
    pdk.Layer(
        "ScatterplotLayer",
        id="points",
        data=df,
        get_position=["Longitude", "Latitude"],
        pickable=True,
        stroked=True,
        filled=True,
        # extruded=False,
        wireframe=True,
        auto_highlight=True,
        get_radius=88000,
        radiusMaxPixels=5,
        radiusMinPixels=4,
        getColor='color'
        # get_line_color=[0,240,0],
        # get_fill_color=[0,240,0]
    ),
]


deck = pdk.Deck(
    views=[view],
    tooltip = {
        "html": "<b>Location:</b> {Place} <br/> <b>Disease:</b> {Disease name}<br/> <b>Pathogen type:</b> "+
        "{Pathogen type}<br/> <b>Casual species:</b> <i>{Causal species}</i><br/><b>Affected species:</b> {Affected species}",
        "style": {
        "backgroundColor": "steelblue",
        "color": "white"
        }
    },
    layers=layers,
    map_provider="carto",
    map_style='light',
    # Note that this must be set for the globe to be opaque
    parameters={"cull": True},
)
st.pydeck_chart(deck)