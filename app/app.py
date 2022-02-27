import streamlit as st
import pandas as pd
import json
import plotly.express as px


@st.cache()
def read_data() -> pd.DataFrame:
    """
    Read the covid data
    """

    df = pd.read_parquet("../data/2021-2022-all-covid-data-through-2022-02-20.parquet")
    df.index = pd.to_datetime(df.index)
    return df


@st.cache()
def read_counties() -> dict:
    """
    Read the counties information into a dictionary for quick loading and user input

    """

    with open("../data/state_counties.json", "r") as f:
        counties_dict = json.load(f)

    return counties_dict


data = read_data()
counties = read_counties()

# the list of fips codes to use as a key.
# We could probably get faster lookups if we make the fips codes the index
fips_list = []

# have to wait to show the county until we get the state
def get_county() -> str:
    """get a state and county from the user with dropdowns"""
    state = st.selectbox(
        label="Choose a State",
        options=counties.keys(),
    )

    # TODO: look at using session sate with a callback for on change to add the item to the dictionary

    # on state change, show the counties
    if state:
        county = st.selectbox("Choose a County", options=counties[state])

        return data.loc[(data["state"] == state) & (data["county"] == county)]


# fips_list.append(# the fips values in the state dictionary)


# use a checkbox to ask if want to add another option
# make a list of dictionaries to store state, county pairs
# or maybe just fips #s a single filter should be faster,
# but then have to lookup each of those rows, but need to do that anyway to get covid data
# going wtih get the fips

# filtered_df = data[data["fips"] == fips]
# filtered_df

filtered_df = get_county()
print(filtered_df)


fig = px.line(filtered_df, x=filtered_df.index, y="cases_avg_per_100k", color="county")
fig
