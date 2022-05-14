import pandas as pd
from prefect import task, Flow
from datetime import timedelta
from prefect.schedules import IntervalSchedule


@task
def read_data(oldest_year: int = 2020, newest_year: int = 2022):
    """Read in csv files of data from the nytimes and concatenate into a single pandas DataFrame.

    Args:
      oldest_year: first year of data to use
      newest_year: most recent year of data to use
    """

    df_dicts = {}  # dictionary to hold the data for each year before concatenation

    for year in range(oldest_year, newest_year + 1):
        df_dicts[f"df_{year}"] = pd.read_csv(
            f"https://raw.githubusercontent.com/nytimes/covid-19-data/master/rolling-averages/us-counties-{year}.csv",
            index_col="date",
        )

    return pd.concat(df_dicts.values())


@task
def write_data(df: pd.DataFrame):
    """write out data frame to parquet file

    Args:
        df: the concatenated data frame
    """

    df.to_parquet(
        f"./data/2020-2022-all-covid-data-through-{df.tail(1).index.values[0]}.parquet"
    )  # 20mb mar 20222


# check every 12 hours
# schedule = IntervalSchedule(interval=timedelta(hours=12))


with Flow("build data") as flow:  # schedule=schedule) as flow:
    df = read_data(2020, 2022)
    write_data(df)

if __name__ == "__main__":
    flow.run()
