from datetime import timedelta
import pandas as pd
import prefect
from prefect import task, Flow
from prefect.schedules import IntervalSchedule
from prefect.engine.results import LocalResult
from prefect.engine.serializers import PandasSerializer


logger = prefect.context.get("logger")


@task
def read_data(oldest_year: int = 2020, newest_year: int = 2022):
    """Read in csv files of yearly covid data from the nytimes and concatenate into a single pandas DataFrame.

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
    logger.info("data read in successfully")
    return pd.concat(df_dicts.values())


@task(
    # result=LocalResult(
    #      dir="/Users/hale/Dropbox/DS/covidcities/data/"
)
# )
def write_data(df: pd.DataFrame):
    """write out data frame to parquet file

    Args:
        df: the concatenated data frame
    """
    # write_val = PandasSerializer(file_type="parquet")
    logger = prefect.context.get("writing data function started")
    # return write_val.serialize(df)

    df.to_parquet(
        f"./data/2020-2022-all-covid-data-through-{df.tail(1).index.values[0]}.parquet"
    )
    # )


with Flow("build data") as flow:
    df = read_data(2020, 2022)
    output = write_data(df)

# check if flow is serializable, passes if True
# from prefect.utilities.debug import is_serializable

# is_serializable(flow)

if __name__ == "__main__":
    state = flow.run()

# runs fine locally when called manually
# now trying on cloud, rereregistered flow
# may need to specify result location and type to run on cloud? but then need to deserialize when read in data later?
# will need a path relative to home directory perhaps
