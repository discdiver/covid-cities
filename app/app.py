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


def get_county() -> str:
    """get a state and county from the user with dropdowns"""

    state = st.selectbox(
        label="Choose a State",
        options=counties.keys(),
        index=5,
    )

    county = st.selectbox(
        "Choose a County",
        options=counties[state],
        index=min(len(counties[state]) - 1, 18),
    )

    return data.loc[(data["state"] == state) & (data["county"] == county), "fips"]


def build_df(fips_list: list) -> pd.DataFrame:
    """filter df to selected rows' fips codes"""

    return data.loc[data["fips"].isin(fips_list)]


st.session_state.concat_df = pd.DataFrame()

fips = get_county()
filtered_df = build_df(fips)

st.session_state.concat_df = pd.concat([st.session_state.concat_df, filtered_df])

fig = px.line(
    data_frame=st.session_state.concat_df,
    x=st.session_state.concat_df.index,
    y="cases_avg_per_100k",
    color="county",
    title="Average cases per 100k, 7-day rolling average",
)
fig.update_yaxes(title="")
fig.update_xaxes(title="")
fig.update_layout(showlegend=False)
fig

st.subheader("Choose another State and County combination above to add to the map")
