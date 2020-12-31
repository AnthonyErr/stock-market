import pandas as pd
from pandas_datareader._utils import RemoteDataError

from typing import Dict
from stock_market.data import IPO, get_ticker


OSD_THRESH = 3


class RecentIPO(object):
    """
    Analysis on Recent IPO stocks (within 3 weeks).
    """

    # Get recent ipo data
    recent_ipo = IPO().recent_ipo

    # Helper variables
    _price_history = None  # Storing stock price history

    # Stats on different views
    _summary = None
    _individual_view = None

    @property
    def summary(self) -> pd.DataFrame:
        """
        High level summary of recent IPOs.
        1) Aggregate stock performance in one percentage.
        2) Total price shift per stocks since IPO
        3) Optimal sell day (Number of market days since IPO where stock price was at highest)

        """
        # Check if summary function has been run
        if self._summary is None:
            # Setup for metric population
            data = self.price_history
            _summary = {}
            ticker_agg_stats = pd.DataFrame()

            # Loop through each tickers
            for ticker in data.keys():
                ticker_data = data[ticker]
                ticker_open = ticker_data.iloc[0, :].Open

                # Calculate Optimal Sell Day (OSD)
                ticker_high = list(ticker_data["High"])
                osd = ticker_high.index(max(ticker_high))

                # Add ticker stats to aggregated stats
                ticker_stats = {
                    "Ticker": ticker,
                    "Pct_Overall_Change": _percent_change(
                        start_value=ticker_open,
                        end_value=ticker_data.iloc[len(ticker_data) - 1, :].Close,
                    ),
                    "OSD": osd,
                    "OSD_Max_Pct_Gain": _percent_change(
                        start_value=ticker_open, end_value=max(ticker_high)
                    ),
                    "OSD_Ongoing": True
                    if len(ticker_high) - OSD_THRESH > osd
                    else True,
                }
                ticker_agg_stats = ticker_agg_stats.append(
                    pd.DataFrame(ticker_stats, index=[0])
                )

            ticker_agg_stats = ticker_agg_stats.reset_index()

    @property
    def price_history(self) -> Dict[str, pd.DataFrame]:
        """
        Stores all recent ipo historical data.
        """

        if self._price_history is None:
            _price_history = {}
            recent_ipo = self.recent_ipo
            today = pd.to_datetime("today")

            for stock_i in range(len(recent_ipo)):
                # Loop through each stock to see validity in US/CDN stock exchange
                try:
                    ticker = recent_ipo.iloc[stock_i, :].Ticker
                    _price_history[ticker] = get_ticker(
                        ticker=ticker, start_date=today - pd.Timedelta(days=30)
                    )
                except RemoteDataError:
                    pass

            self._price_history = _price_history

        return self._price_history


# Helper function
def _percent_change(
    start_value: float, end_value: float, to_percent: bool = True
) -> float:
    """
    Calculates percent change of two values.

    Parameters
    ----------
    start_value: float
        Start value.

    end_value: str
        End value.

    to_percent: bool;, default True
        Option to output value as percentage.

    Returns
    -------
    percent_change: float
        Percent change between start and end value.

    """
    # Percent or decimal value
    multiplier = 100.0 if to_percent else 1.0

    # Calculation
    percent_change = (end_value - start_value) / start_value * multiplier

    return percent_change
