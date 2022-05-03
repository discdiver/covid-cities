import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import date, timedelta
from pathlib import Path
import humanize

st.set_page_config(page_title="COVID case data", page_icon="📉", layout="wide")

st.title("COVID-19 Cases")
st.subheader("See COVID prevalence for US locations you care about")


@st.cache()
def get_most_recent_data():
    """get the date from most recent covid data file

    Returns:
    """

    path = Path("./data")

    date_to_check = date.today()

    # only look back a few days, if not found, something is messed up, return as soon as found
    for _ in range(10):
        for file in path.rglob("*.parquet"):
            if str(date_to_check) in str(file):
                return str(file), date_to_check

        date_to_check = date_to_check - timedelta(days=1)
    # no recent files found/return an old file
    return (
        "./data/2020-2022-all-covid-data-through-2022-04-02.parquet",
        date_to_check,
    )


@st.cache()
def read_data():
    """
    Read the most recent covid data into the app
    """

    (data_path, most_recent_date) = get_most_recent_data()

    df = pd.read_parquet(data_path)
    df.index = pd.to_datetime(df.index)
    return df, most_recent_date


@st.cache()
def read_counties() -> dict:
    """
    Read the counties information into a dictionary for quick loading and user input
    """

    with open("./data/state_counties.json", "r") as f:
        counties_dict = json.load(f)

    return counties_dict


data, most_recent_date = read_data()
counties = read_counties()

# get user input and store in session state so can add multiple locations
choose_state = st.selectbox(
    label="Choose a State",
    options=counties.keys(),
    index=9,  # default to District of Columbia
)

county_key = st.selectbox(
    "Choose a County",
    options=counties[choose_state],
    index=min(len(counties[choose_state]) - 1, 0),  # default to first county (DC)
)

if "county_list" not in st.session_state:
    st.session_state["county_list"] = []


def add_state_and_county_to_session_state():
    """Add new state, country to session state"""

    if (choose_state, county_key) not in st.session_state["county_list"]:
        st.session_state["county_list"].append((choose_state, county_key))


# style button using theme colors
primaryColor = st.get_option("theme.primaryColor")

s = f"""
<style>
div.stButton > button:first-child {{ border: 3px solid {primaryColor}; border-radius:20px 20px 20px 20px; }}
<style>
"""
st.markdown(s, unsafe_allow_html=True)
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


filtered_df = get_county(choose_state)

filtered_df.tail(10)

# get the starting date
start_date = st.date_input(
    "Start date",
    value=date(2022, 1, 1),
    min_value=date(2019, 2, 24),
    max_value=most_recent_date,  # found when check for most recent file
)

start_date = pd.to_datetime(start_date).to_period("D")
filtered_df = filtered_df.loc[str(start_date) :]


try:
    if "county_list" in st.session_state:

        # clean up column names
        filtered_df["Location"] = filtered_df["county"] + ", " + filtered_df["state"]
        filtered_df.rename(
            columns={
                "date": "Date",
                "cases_avg_per_100k": "Cases per 100,000, 7-day rolling average",
            },
            inplace=True,
        )

        # plot
        fig = px.line(
            data_frame=filtered_df,
            x=filtered_df.index,
            y="Cases per 100,000, 7-day rolling average",
            color="Location",
            title="Cases per 100,000 population, 7-day rolling average",
        )

        # set axes to 0, round to nearest 100 more
        y_max = filtered_df["Cases per 100,000, 7-day rolling average"].max()

        y_max -= y_max % -100

        fig.update_yaxes(
            title="",
            range=[0, y_max],
        )

        fig.update_xaxes(title="")
        fig.update_traces(hovertemplate="%{y} cases")
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # make table
        st.subheader(
            f"Data for {humanize.naturalday(most_recent_date)} ({most_recent_date})"
        )

        # CSS to inject contained in a string - hide index - from streamlit docs
        hide_table_row_index = """
                    <style>
                    tbody th {display:none}
                    .blank {display:none}
                    </style>
                    """

        # inject CSS with Markdown
        st.markdown(hide_table_row_index, unsafe_allow_html=True)

        # filter to most recent date
        most_recent_date = str(filtered_df.index.max())[:11]
        most_recent_cases = filtered_df.query("index==@most_recent_date")[
            ["Location", "Cases per 100,000, 7-day rolling average"]
        ]

        st.table(
            most_recent_cases.sort_values(
                by="Cases per 100,000, 7-day rolling average", ascending=False
            ).style.format({"Cases per 100,000, 7-day rolling average": "{:,.2f}"})
        )

        # could add % change since last week


except Exception as e:
    print(e)
    pass


def clear_plot():
    """clear session state"""
    st.session_state = {}


# display button to clear plot and suggestion to pick more counties if plot exists
if st.session_state["county_list"]:

    st.subheader("Add additional locations above to compare! 🙂")

    st.markdown("""---""")
    # st.button("Start over?", on_click=clear_plot)

    # st.markdown("""---""")
    st.write(
        "App source: [Jeff Hale's GitHub Repository](https://github.com/discdiver/covid-cities) |  [County mapping source](https://simplemaps.com/data/us-counties.) |\
         Data source: [New York Times](https://github.com/nytimes/covid-19-data/tree/master/rolling-averages) "
    )
    st.write(
        "Note: data is subject to test availability, individual reporting, and local government reporting - it is highly imperfect. \
        The New York Times chose to report some data by county and some by city."
    )
