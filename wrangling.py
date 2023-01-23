import pandas as pd
import click
import logging, click_logging
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
click_logging.basic_config(logger)


@click.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option("--output-path", type=click.Path(path_type=Path), default="./output.csv")
def wrangle(input_path: Path(), output_path: Path()):
    logger.info("read in the data")
    df = pd.read_excel(io=input_path, sheet_name="1a", skiprows=4)

    logger.info("extract features")
    df = df.join(df["Time period"].str.split(" to ", expand=True))

    logger.info("rename columns from 0 and 1")
    df = df.rename(columns={0: "start_date", 1: "end_date"})

    logger.info("Convert start_date, end_date to datetime")
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])

    df["period_length"] = (df["end_date"] - df["start_date"]).dt.days

    # df["period"] = df["start_date"].strftime("%Y-%m-%dT00:00:00").apply(lambda x: x + "/P")
    # TODO: THE NONSENSE ABOVE

    logger.info("Convert start_date to Week ISO format")
    df["week"] = (
        df["start_date"]
        .dt.year.astype(str)
        .str.cat(df["start_date"].dt.isocalendar().week.astype(str), sep="-W")
    )

    logger.info("Rename observation columns")
    rename_columns = {
        r"Estimated average % of the population testing positive for COVID-19": "percentage_pop_est",
        r"95% Lower confidence/credible interval for percentage": "percentage_pop_est_lci",
        r"95% Upper confidence/credible interval for percentage": "percentage_pop_est_uci",
        r" Estimated average number of people testing positive for COVID-19": "pop_est",
        r"95% Lower confidence/credible interval for number": "pop_est_lci",
        r"95% Upper confidence/credible interval for number": "pop_est_uci",
    }
    df = df.rename(columns=rename_columns)

    logger.info(
        "Drop duplicates based on week, assume last value is most recent NOT VALID FOR ANALYSIS"
    )
    df.drop_duplicates(subset="week", keep="last", inplace=True)

    logging.info("Adding geography code for England")
    df["ons_geog_code"] = "E92000001"

    logger.info("Project & save as csv")
    df[
        [
            "week",
            "ons_geog_code",
            "percentage_pop_est",
            "percentage_pop_est_lci",
            "percentage_pop_est_uci",
            "pop_est",
            "pop_est_lci",
            "pop_est_uci",
        ]
    ].to_csv(output_path, index=False)


if __name__ == "__main__":
    wrangle()
