import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import date, timedelta
from pathlib import Path
import humanize

st.title("COVID-19 Case data")
st.subheader("See COVID prevalence in the places you care about 🙂")


@st.cache()
def get_most_recent_data():
    """get the date from most recent covid data file"""
    path = Path("../data")

    date_to_check = date.today()

    # only look back a few days, if not found, something is messed up
    for _ in range(10):
        for file in path.rglob("*.parquet"):
            if str(date_to_check) in str(file):
                return str(file), date_to_check

        date_to_check = date_to_check - timedelta(days=1)
    return (
        "../data/2020-2022-all-covid-data-through-2022-03-18.parquet",
        date_to_check,
    )


@st.cache()
def read_data() -> pd.DataFrame:
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

    with open("../data/state_counties.json", "r") as f:
        counties_dict = json.load(f)

    return counties_dict


data, most_recent_date = read_data()
counties = read_counties()

# get user input and store in session state so can add multiple locations
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


filtered_df = get_county(choose_state)

filtered_df.tail(10)

# get the starting date
start_date = st.date_input(
    "Start date",
    value=date(2021, 6, 1),
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
        fig.update_yaxes(title="")
        fig.update_xaxes(title="")

        fig.update_layout(legend_title_text="Location", hovermode="x")

        st.plotly_chart(fig)

        # make table
        st.subheader(
            f"Data for {humanize.naturalday(most_recent_date)}, ({most_recent_date})"
        )

        # CSS to inject contained in a string - hide index - from streamlit docs
        hide_table_row_index = """
                    <style>
                    tbody th {display:none}
                    .blank {display:none}
                    </style>
                    """

        # Inject CSS with Markdown
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

    st.subheader("Choose another location above to add to the map")

    st.markdown("""---""")
    # st.button("Start over?", on_click=clear_plot)

    # st.markdown("""---""")
    st.write(
        "App source: [Jeff Hale's GitHub Repository](https://github.com/discdiver/covid-cities) |  \
         Data source: [New York Times](https://github.com/nytimes/covid-19-data/tree/master/rolling-averages) "
    )
    st.write(
        "Note: data is subject to test availability and local reporting. \
    The New York Times chose to report some data by county and some by city."
    )


# TODO add functionality to create user account to login and store favorites
