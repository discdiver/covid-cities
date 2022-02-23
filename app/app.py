import streamlit as st
import pandas as pd
import json


def read_data() -> pd.DataFrame:
    """
    Read the data
    """

    df = pd.read_feather("../data/2021-2022-all-covid-data-through-2022-02-20.feather")
    return df


def read_counties() -> dict:
    """
    Read the counties information into a dictionary

    """

    with open("../data/state_counties.json", "r") as f:
        counties_dict = json.load(f)

    return counties_dict


data = read_data()
counties = read_counties()

state = st.selectbox("Choose a State", options=counties.keys())


county = st.selectbox("Choose a County", options=counties[state])
