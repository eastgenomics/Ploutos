import pandas as pd
import plotly.graph_objects as go

from collections import defaultdict
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from dashboard.models import DailyOrgRunningTotal
from scripts import DNAnexus_queries as dx_queries


class RunningTotPlotFunctions():
    """Class for plotting functions for the running total graph"""

    def __init__(self) -> None:
        # Get all DailyOrgRunningTotal objects as a queryset
        # So multiple db queries not needed
        self.totals = DailyOrgRunningTotal.objects.all()

    def calculate_diffs(self, tuple_of_charges):
        """
        Creates list of charge differences
        Where one charge is subtracted from the previous date
        Parameters
        ----------
        tuple_of_charges :  tuple
            date-sorted tuple of charges for a specific charge type

        Returns
        -------
        charge_diff : list
            list with charge differences from the previous day
        """
        charge_diff = [
            y - x for x, y in zip(tuple_of_charges, tuple_of_charges[1:])
        ]

        return charge_diff

    def daily_plot(self, totals):
        """
        Set bar chart context for daily running charges plot
        Parameters
        ----------
        totals : queryset
            queryset already filtered by default or specified daterange

        Returns
        -------
        fig : Plotly figure object
        """

        # Order filtered DailyOrgRunningTotal objects by date and get charges
        charges = totals.order_by(
            'date__date'
        ).values_list(
            'storage_charges', 'compute_charges', 'egress_charges'
        )

        # Get dates in order from db
        dates = totals.order_by('date__date').values_list(
            'date__date', flat=True
        )

        # Turn date objects into strings
        stringified_dates = [str(date) for date in dates][:-1]
        # If there are charges in the db for those dates
        if charges:
            # Get the relevant info for each charge type as a list
            storage_charges, compute_charges, egress_charges = zip(*charges)

            # Calculate a date's charges minus previous date
            storage_charge_diff = self.calculate_diffs(storage_charges)
            compute_charge_diff = self.calculate_diffs(compute_charges)
            egress_charge_diff = self.calculate_diffs(egress_charges)
        else:
            storage_charge_diff = []
            compute_charge_diff = []
            egress_charge_diff = []

        # Turn this into df to use for DataTables
        daily_charge_df = pd.DataFrame(
            {
                'Date': stringified_dates,
                'Storage charges ($)': storage_charge_diff,
                'Compute charges ($)': compute_charge_diff,
                'Egress charges ($)': egress_charge_diff
            }
        )

        daily_df = daily_charge_df.to_html(
            index=False,
            classes='table table-striped" id = "dailytable',
            justify='left',
            float_format="%.3f"
        )

        if storage_charge_diff:
            # Add unified hover label so all charges shown
            fig = go.Figure(
                layout={
                    'hovermode': 'x unified'
                }
            )

            fig.add_trace(go.Bar(
                x=stringified_dates,
                y=compute_charge_diff,
                name='Compute',
                hovertemplate='%{y:.2f}'
                )
            )

            fig.add_trace(go.Bar(
                x=stringified_dates,
                y=storage_charge_diff,
                name='Storage',
                hovertemplate='%{y:.2f}'
                )
            )

            fig.add_trace(go.Bar(
                x=stringified_dates,
                y=egress_charge_diff,
                name='Egress',
                hovertemplate='%{y:.2f}'
                )
            )

            fig.update_layout(
                title={
                    'text': "Daily Running Charges",
                    'xanchor': 'center',
                    'x': 0.5,
                    'font_size': 20
                },
                xaxis_title="Date",
                xaxis_tickformat='%d %b %y',
                yaxis_title="Daily estimated charge ($)",
                yaxis_tickformat=",d",
                barmode='stack',
                width=1200,
                height=600,
                font_family='Helvetica',
            )

            # Add black border to bars
            fig.update_traces(
                marker_line_color='rgb(0,0,0)',
                marker_line_width=1
            )

            fig.update_yaxes(rangemode="nonnegative")

        else:
            fig = go.Figure()
            fig.update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False},
                width=1200,
                height=600,
                annotations=[
                    {
                        "text": "No data to display",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {
                            "size": 20
                        }
                    }
                ]
            )

        return fig, daily_df

    def monthly_between_dates(self, start_month, end_month):
        """
        Set context for the monthly graph between start_month and end_month
        Parameters
        ----------
        start_month :  datetime.date object
            date in YYY-MM-DD format e.g. "2022-05-01" as first date in range
        end_month : datetime.date object
            date in YYY-MM-DD format e.g. "2022-06-01" as last date in range

        Returns
        -------
        chart : Plotly figure object converted to HTML
        """
        # Filter between start of start_month
        # And 1st of the month that comes after end_month
        monthly_charges = self.totals.filter(
            date__date__range=[
                start_month, end_month
            ]
        ).values_list(
            'date__date__month',
            'date__date__year',
            'storage_charges',
            'compute_charges',
            'egress_charges'
        )

        # Convert the end month from e.g. '2022-07-01' to '07-2022'
        # To check if it exists later
        check_end_month = datetime.strftime(end_month, "%m-%Y")

        storage_dic = defaultdict(list)
        compute_dic = defaultdict(list)
        egress_dic = defaultdict(list)
        months = []
        storage_charges = []
        compute_charges = []
        egress_charges = []

        # Make each a defaultdict e.g. {'5-2022': [500.20, 100.40]}
        for item in monthly_charges:
            storage_dic[f"0{item[0]}-{item[1]}"].append(item[2])
            compute_dic[f"0{item[0]}-{item[1]}"].append(item[3])
            egress_dic[f"0{item[0]}-{item[1]}"].append(item[4])

        # Get the keys and sort by month-year
        # Only need to do this for storage_dic as all have same keys
        key_list = sorted(
            storage_dic.keys(),
            key=lambda x: datetime.strptime(x, '%m-%Y')
        )

        current_month = datetime.strftime(date.today(), "%m-%Y")
        # If the end month is for the 1st of next month
        # The month won't exist as a key in the dict
        # Instead take the last entry of the current month
        # To act as the 1st of the next month in its place
        if check_end_month not in key_list:
            if current_month in key_list:
                storage_dic.update({
                    check_end_month: [storage_dic[key_list[-1]][-1]]
                })
                compute_dic.update({
                    check_end_month: [compute_dic[key_list[-1]][-1]]
                })
                egress_dic.update({
                    check_end_month: [egress_dic[key_list[-1]][-1]]
                })

        # Get the keys (months as e.g. '05-2022') again as list
        # As may include next month now
        key_list = sorted(
            storage_dic.keys(),
            key=lambda x: datetime.strptime(x, '%m-%Y')
        )

        # Append the first charge of each month to lists
        for month in key_list:
            months.append(month)
            storage_charges.append(storage_dic[month][0])
            compute_charges.append(compute_dic[month][0])
            egress_charges.append(egress_dic[month][0])

        # Calculate the charge differences between months
        if storage_charges:
            storage_charges = self.calculate_diffs(storage_charges)
        if compute_charges:
            compute_charges = self.calculate_diffs(compute_charges)
        if egress_charges:
            egress_charges = self.calculate_diffs(egress_charges)

        # Remove the last month from the month categories
        # That we are taking the 1st date from but not using
        if months:
            months = months[:-1]

        # Convert months to strings e.g. "May 2022" for plotting
        converted_months = [
            (datetime.strptime(month, "%m-%Y").strftime('%b %Y'))
            for month in months
        ]

        # Turn this into df to use for DataTables
        monthly_charge_df = pd.DataFrame(
            {
                'Month': converted_months,
                'Storage charges ($)': storage_charges,
                'Compute charges ($)': compute_charges,
                'Egress charges ($)': egress_charges
            }
        )

        if monthly_charge_df.empty:
            monthly_df = monthly_charge_df.to_html(
            index=False,
            classes='table table-striped" id = "monthlytable',
            justify='left'
        )

        else:
            monthly_df = monthly_charge_df.to_html(
                index=False,
                classes='table table-striped" id = "monthlytable',
                justify='left',
                float_format="%.3f"
            )

        if storage_charges:
            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=converted_months,
                y=compute_charges,
                name='Compute',
                hovertemplate=(
                    '<br>Month: %{x}<br>Charge: $%{y:.2f}<br>'
                    '<extra></extra>'
                ),
                marker=dict(color='#636EFA')
                )
            )

            fig.add_trace(
                go.Bar(
                    x=converted_months,
                    y=storage_charges,
                    name='Storage',
                    hovertemplate=(
                        '<br>Month: %{x}<br>Charge: $%{y:.2f}<br>'
                        '<extra></extra>'
                    ),
                    marker=dict(color='#EF553B')
                )
            )

            fig.add_trace(
                go.Bar(
                    x=converted_months,
                    y=egress_charges,
                    name='Egress',
                    hovertemplate=(
                        '<br>Month: %{x}<br>Charge: $%{y:.2f}<br>'
                        '<extra></extra>'
                    ),
                    marker=dict(color="#00CC96")
                )
            )

            fig.update_layout(
                title={
                    'text': "Monthly Running Charges",
                    'xanchor': 'center',
                    'x': 0.5,
                    'font_size': 20
                },
                xaxis_title="Month",
                xaxis_tickformat='%d %b %y',
                yaxis_title="Monthly estimated charge ($)",
                yaxis_tickformat=",d",
                width=1200,
                height=600,
                font_family='Helvetica'
            )

            fig.update_yaxes(rangemode="nonnegative")

            # Add black border to bars
            fig.update_traces(
                marker_line_color='rgb(0,0,0)',
                marker_line_width=1,
            )

        else:
            fig = go.Figure()
            fig.update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False},
                width=1200,
                height=600,
                annotations = [
                    {
                        "text": "No data to display",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {
                            "size": 20
                        }
                    }
                ]
            )

        chart = fig.to_html()

        return chart, monthly_df
