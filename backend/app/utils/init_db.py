from typing import Optional

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.deps import get_db


def drop_table_with_cascade(table_name: str, session: Session):
    """
    Drops a table with CASCADE to remove dependent objects.
    """
    session.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
    session.commit()


def df_to_db(
    df: pd.DataFrame,
    table_name: str,
    if_exists: str = "append",
    chunksize: Optional[int] = 1000,
):
    """
    Inserts a Pandas DataFrame into the specified database table synchronously.

    Parameters:
        df (pd.DataFrame): The DataFrame to insert into the database.
        table_name (str): The name of the database table.
        if_exists (str): Behavior when the table already exists ('fail', 'replace', 'append').
        chunksize (Optional[int]): The number of rows to insert at a time.

    Returns:
        None
    """
    print(f"Starting data insertion into table: {table_name}")

    # Use the session provided by get_db
    db_generator = get_db()
    session = next(db_generator)  # Get the session from the generator

    try:
        if if_exists == "replace":
            # Drop the table with CASCADE
            drop_table_with_cascade(table_name, session)
        # Use the session's connection to write the DataFrame to the database
        with session.begin():
            conn = session.connection()
            try:
                df.to_sql(
                    name=table_name,
                    con=conn,
                    index=True,  # Assuming the DataFrame index should be used
                    if_exists=if_exists,
                    chunksize=chunksize,
                )
                print(f"Data successfully inserted into table: {table_name}")
            except Exception as e:
                print(f"Error during data insertion into table {table_name}: {e}")
                raise
    finally:
        next(db_generator, None)  # Close the session

    print(f"Data insertion process for table {table_name} completed.")


def gdf_to_db(
    gdf: gpd.GeoDataFrame,
    table_name: str,
    if_exists: str = "append",
    chunksize: int = 1000,
    index: bool = True,
):
    """
    Inserts a GeoPandas GeoDataFrame into the specified PostGIS table synchronously.

    Parameters:
        gdf (gpd.GeoDataFrame): The GeoDataFrame to insert into the database.
        table_name (str): The name of the database table.
        if_exists (str): Behavior when the table already exists ('fail', 'replace', 'append').
        chunksize (int): The number of rows to insert at a time.
        index (bool): Whether to write the GeoDataFrame index as a column.

    Returns:
        None
    """
    if gdf.crs is None:
        raise ValueError(
            "The GeoDataFrame must have a defined CRS. Use gdf.set_crs() to set one."
        )

        # Ensure all geometries are MultiPolygon
    gdf["geometry"] = gdf["geometry"].apply(
        lambda geom: MultiPolygon([geom]) if isinstance(geom, Polygon) else geom
    )

    print(f"Starting data insertion into table: {table_name}")

    # Use the session provided by get_db
    db_generator = get_db()
    session = next(db_generator)  # Get the session from the generator

    try:
        if if_exists == "replace":
            # Drop the table with CASCADE
            drop_table_with_cascade(table_name, session)
        # Use the session's connection to write the GeoDataFrame to the database
        with session.begin():
            conn = session.connection()
            try:
                gdf.to_postgis(
                    name=table_name,
                    con=conn,
                    if_exists=if_exists,
                    index=index,
                    chunksize=chunksize,
                )
                print(f"Data successfully inserted into table: {table_name}")
            except Exception as e:
                print(f"Error during data insertion into table {table_name}: {e}")
                raise
    finally:
        next(db_generator, None)  # Close the session

    print(f"Data insertion process for table {table_name} completed.")
