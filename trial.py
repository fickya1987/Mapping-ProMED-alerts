import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
import pydeck as pdk


# REFERENCES
# https://deckgl.readthedocs.io/en/latest/gallery/globe_view.html
# https://deck.gl/docs/
# https://python.plainenglish.io/building-lightweight-geospatial-data-viewers-with-streamlit-and-pydeck-de1e0fbd7ba7

# print(pd.DataFrame(columns=[':as','asdasd']))
# data = pd.DataFrame({
#         'latitude':[37.7749,34.0522,40.7128,28.6138954],
#         'longitude':[-122.4194,-118.2437,-74.0060,77.2090057],
#         'name':['SF',"Los Angeles","New York","Delhi"]
# })
# Create map
# st.map(data)

# Querying a geolocator for every instance will not be feasible. Moreover, that is not the primary objective of this.
# Thus, a better approach might be to save the latitude and longitude of each instance of promed alert in the accompanying
# Excel file itself.
# locator = Nominatim(user_agent="Mapping")



COUNTRIES = "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_scale_rank.geojson"
# POWER_PLANTS = "https://raw.githubusercontent.com/ajduberstein/geo_datasets/master/global_power_plant_database.csv"



# df = pd.read_csv(POWER_PLANTS)


# def is_green(fuel_type):
#     """Return a green RGB value if a facility uses a renewable fuel type"""
#     if fuel_type.lower() in ("nuclear", "water", "wind", "hydro", "biomass", "solar", "geothermal"):
#         return [10, 230, 120]
#     return [230, 158, 10]


# df["color"] = df["primary_fuel"].apply(is_green)

# view_state = pdk.ViewState(latitude=51.47, longitude=0.45, zoom=2, min_zoom=2)

# Set height and width variables
view = pdk.View(type="_GlobeView", controller=True, width=1000, height=700)


data = pd.read_excel("tracker.xlsx")

Lats = list()
Lons = list()
loca = list()
def getLatLon(addr):
    l = addr.split(", ")
    lat = float(l[-2])
    lon = float(l[-1])
#     return lat,lon
    Lats.append(lat)
    Lons.append(lon)
    loca.append(l[:-2])

# lats,lons = 
data["Location"].apply(getLatLon)

# st.write(Lats,Lons)
data['latitude'] = Lats
data['longitude'] = Lons
data['name'] = [", ".join(i) for i in loca]

layers = [
    pdk.Layer(
        "GeoJsonLayer",
        id="base-map",
        data=COUNTRIES,
        stroked=False,
        filled=True,
        get_fill_color=[200, 200, 200],
    ),
    pdk.Layer(
        "ColumnLayer",
        id="power-plant",
        data=data,
        # get_elevation="capacity_mw",
        get_position=["longitude", "latitude"],
        # elevation_scale=100,
        pickable=True,
        stroked=True,
        filled=True,
        opacity=0.8,
        auto_highlight=True,
        # radius_scale=6,
        radius=80000,
        get_fill_color=[0,240,0]#"color",
    ),
]

deck = pdk.Deck(
    views=[view],
#     initial_view_state=view_state,
#     tooltip={"text": "{name}, {primary_fuel} plant, {country}"},
#     tooltip={"text":"{name}"},
    tooltip = {
        "html": "<b>Location:</b> {name} <br/> <b>Disease:</b> {Disease name}<br/> <b>Pathogen type:</b> "+
        "{Pathogen type}<br/> <b>Casual species:</b> {Causal species}<br/><b>Affected species:</b> {Affected species}",
        "style": {
        "backgroundColor": "steelblue",
        "color": "white"
        }
    },
    layers=layers,
    map_provider=None,
    # Note that this must be set for the globe to be opaque
    parameters={"cull": True},
)
st.pydeck_chart(deck)