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
st.session_state[f"{choose_state}-{county_key}"] = True


def get_county(state) -> str:
    """filter to state and county to plot"""

    # make a dictionary of key, value pairs from session state
    state_county_choices = {
        k.split("-")[0]: k.split("-")[1]
        for k, v in st.session_state.items()
        if v == True
    }

    # build the dataframe
    df = pd.DataFrame()

    for state, county in state_county_choices.items():
        df = pd.concat(
            [df, data.loc[(data["state"] == state) & (data["county"] == county)]]
        )
    return df


filtered_df = get_county(choose_state)  # get county from user

print(filtered_df)

fig = px.line(
    data_frame=filtered_df,
    x=filtered_df.index,
    y="cases_avg_per_100k",
    color="county",
    title="Average cases per 100k, 7-day rolling average",
)
fig.update_yaxes(title="")
fig.update_xaxes(title="")
fig

st.subheader("Choose another State and County combination above to add to the map")
