import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import date


@st.cache()
def read_data() -> pd.DataFrame:
    """
    Read the covid data
    """

    ## TODO try to read today's data
    # if that dowsn't work, go back one day earlier until find working date

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

choose_state = st.selectbox(
    label="Choose a State",
    options=counties.keys(),
    index=5,
)

county_key = st.selectbox(
    "Choose a County",
    options=counties[choose_state],
    index=min(len(counties[choose_state]) - 1, 18),
)

if "county_list" not in st.session_state:
    st.session_state["county_list"] = []


def add_state_and_county_to_session_state():
    """Add new state, country to session state"""

    if (choose_state, county_key) not in st.session_state["county_list"]:
        st.session_state["county_list"].append((choose_state, county_key))


st.button("Add to plot?", on_click=add_state_and_county_to_session_state)


def get_county(state: str):
    """filter data frame to state and county pairs to plot

    Args:
        state: the US state or territory"""

    df = pd.DataFrame()

    if "county_list" in st.session_state:
        for state, county in st.session_state["county_list"]:
            df = pd.concat(
                [
                    df,
                    data.loc[(data["state"] == state) & (data["county"] == county)],
                ]
            )
        return df


# get county from user
filtered_df = get_county(choose_state)

# get the starting date
# TODO change max_value to most recent file
start_date = st.date_input(
    "Start date",
    value=date(2021, 6, 1),
    min_value=date(2019, 2, 24),
    max_value=date.today(),
)

start_date = pd.to_datetime(start_date).to_period("D")
filtered_df = filtered_df.loc[str(start_date) :]

# maybe add end date

# make the plot
try:
    if "county_list" in st.session_state:
        fig = px.line(
            data_frame=filtered_df,
            x=filtered_df.index,
            y="cases_avg_per_100k",
            color="county",
            title="Average cases per 100k, 7-day rolling average",
        )
        fig.update_yaxes(title="")
        fig.update_xaxes(title="")

        # TODO update legend and tooltip to have state in addition to city
        st.plotly_chart(fig)

except:
    pass


def clear_plot():
    """clear session state"""
    st.session_state = {}


# display button to clear plot and suggestion to pick more counties if plot exists
if st.session_state["county_list"]:
    st.button("Clear plot?", on_click=clear_plot)
    st.subheader("Choose another State and County combination above to add to the map")


# add functionality to login and store favorites
