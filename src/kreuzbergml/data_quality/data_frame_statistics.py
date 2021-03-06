from enum import Enum, auto
from logging import getLogger
from typing import List, Optional, Union

from pandas import DataFrame, DatetimeIndex, Index, PeriodIndex, date_range, period_range

logger = getLogger(__name__)


class DataFrameStatistics:

    def __init__(self,
                 df: DataFrame
                 ):
        self._df = df

        if isinstance(self._df.index, DatetimeIndex):
            self._df_type = "time"
        elif isinstance(self._df.index, PeriodIndex):
            self._df_type = "period"
        else:
            self._df_type = "tabular"

    @property
    def df(self):
        return self._df

    def count_nulls(self, col: Union[List[str], str, None] = None):
        """
        :param col: column name if provided only counts null in that column
        :return:
            count of null values,
        """
        count = self.df.isnull().sum() if col is None else self.df[col].isnull().sum()
        return count

    def get_null_cols(self, col: Optional[str] = None) -> List[str]:
        """
        :param col: if given, checks if  col(s) has nulls
        :return:
            list of given column(s) or all columns with null values in DataFrame if None."
        """
        return list(self.df.columns[self.count_nulls() > 0]) if col is None \
            else col if isinstance(col, list) \
            else [col]

    def get_duplicate_columns(self):
        """
        :return:
            Returns a mapping dictionary of columns with fully duplicated feature values
        """
        dupes = {}
        for idx, col in enumerate(self.df.columns):  # Iterate through all the columns of dataframe
            ref = self.df[col]  # Take the column values as reference.
            for tgt_col in self.df.columns[idx + 1:]:  # Iterate through all other columns
                if ref.equals(self.df[tgt_col]):  # Take target values
                    dupes.setdefault(col, []).append(tgt_col)  # Store if they match
        return dupes

    def calc_statistics(self):

        if self._df_type in ["time", "period"]:
            num_missing_dates = len(self.get_missing_indices())
            duplicate_rows = self.df[self.df.duplicated()]

            return {"missing_dates": num_missing_dates, "dup_rows": duplicate_rows}

        else:
            duplicate_cols_dict = self.get_duplicate_columns()
            null_cols = self.get_null_cols()

            return {"dup_cols": duplicate_cols_dict,  "null_cols": null_cols}

    def print_report(self):
        """
        returns a string report containing all the warnings detected during the data quality analysis.
        """
        stats_dict = self.calc_statistics()

        print(f"\n\nDATA QUALITY REPORT\n")

        if self._df_type in ["time", "period"]:
            num_missing_dates = stats_dict['missing_dates']
            duplicate_rows = stats_dict["dup_rows"]
            print(f"Found {num_missing_dates} missing dates in the timeseries index")
            print(f"Found {len(duplicate_rows)} duplicate rows : \n {duplicate_rows}")
        else:
            duplicate_cols_dict = stats_dict['dup_cols']
            null_cols = stats_dict['null_cols']
            num_cols_with_dupes = len(duplicate_cols_dict.keys())
            if num_cols_with_dupes > 0:
                print(f"Found {num_cols_with_dupes} columns with exactly the same feature values as other columns.")
                for col, dupe in duplicate_cols_dict.items():
                    print(f"Columns {dupe} is/are duplicate(s) of Column '{col}'")
            else:
                print("No duplicate columns were found.")

            if len(null_cols) > 0:
                print(f"The following columns have NaN values:")
                for col in null_cols:
                    count = self.count_nulls(col)
                    percentage_nulls = count / len(self.df)

                    print(f"Column '{col}' has {count} NaN values which comprise {percentage_nulls:.2f} of all rows")
            else:
                print(f"No NaN values were found")

    def get_missing_indices(self):
        """
        :return:
            Returns Index with elements that are not in the dataframe index
        """
        min_date = self.df.index.min()
        max_date = self.df.index.max()
        freq = self.df.index.freq

        if self._df_type == "period":
            missing_dates = period_range(start=min_date, end=max_date, freq=freq).difference(self.df.index)
        else:
            missing_dates = date_range(start=min_date, end=max_date, freq=freq).difference(self.df.index)

        return missing_dates
