"""This script holds plotting functions used in views.py"""

import calendar
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from collections import defaultdict
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from dashboard.models import StorageCosts, DailyOrgRunningTotal
from django.conf import settings
from django.db.models import Sum
from scripts import DNAnexus_queries as dx_queries


class RunningTotPlotFunctions():
    """Class for plotting functions for the running total graph"""

    def __init__(self) -> None:
        self.today_date = dx_queries.no_of_days_in_month()[0]
        self.four_months_ago = date.today() + relativedelta(months=-4)
        self.start_of_four_months_ago = self.four_months_ago.replace(day=1)
        self.start_of_next_month = (
            date.today() + relativedelta(months=+1)
        ).replace(day=1)

        # Get all DailyOrgRunningTotal objects as a queryset
        # So multiple db queries not needed
        self.totals = DailyOrgRunningTotal.objects.all()

    def calculate_diffs(self, list_of_charges):
        """
        Creates list of charge differences
        Where one charge is subtracted from the previous date
        Parameters
        ----------
        list_of_charges :  list
            date-sorted list of charges for a specific charge type

        Returns
        -------
        charge_diff : list
            list with charge differences from the previous day
        """
        charge_diff = [
            y - x for x, y in zip(list_of_charges, list_of_charges[1:])
        ]

        return charge_diff

    def daily_plot(self, totals):
        """
        Set bar chart context when all charge types are searched for
        Parameters
        ----------
        totals :  queryset
            queryset already filtered by default or specified daterange

        Returns
        -------
        fig : Plotly figure object
        """

        # Order the DailyOrgRunningTotal objects by date and get charges
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

        # Get the relevant info for each charge type as a list
        storage_charges, compute_charges, egress_charges = zip(*charges)

        # Calculate a date's charges minus previous date
        storage_charge_diff = self.calculate_diffs(storage_charges)
        compute_charge_diff = self.calculate_diffs(compute_charges)
        egress_charge_diff = self.calculate_diffs(egress_charges)

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
                'font_size': 24
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
            marker_line_color = 'rgb(0,0,0)',
            marker_line_width = 1
        )

        return fig

    def monthly_between_dates(self, start_month, end_month):
        """
        Set context for the monthly graph when no dates entered
        Defaults to previous three months
        Parameters
        ----------
        start_month :  str or datetime.date object
            date in YYY-MM-DD format e.g. "2022-05-01" as first date in range
        end_month : str or datetime.date object
            date in YYY-MM-DD format e.g. "2022-06-01" as first date in range

        Returns
        -------
        chart : Plotly figure object converted to HTML
        """
        # Filter between start of start_month and the 1st of the month
        # After end_month
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
            key = lambda x: datetime.strptime(x, '%m-%Y')
        )

        # If the end month is for the 1st of next month
        # The month won't exist as a key in the dict
        # Instead take the last entry of the current month
        # To act as the 1st of the next month in its place
        if check_end_month not in key_list:
            storage_dic.update({
                check_end_month: [storage_dic[key_list[-1]][-1]]
            })
            compute_dic.update({
                check_end_month: [compute_dic[key_list[-1]][-1]]
            })
            egress_dic.update({
                check_end_month: [egress_dic[key_list[-1]][-1]]
            })

        # Get the keys (months as e.g. '05-2022') again
        # As may include next month now
        key_list = sorted(
            storage_dic.keys(),
            key = lambda x: datetime.strptime(x, '%m-%Y')
        )

        # Append the first charge of each month to lists
        for idx, month in enumerate(key_list):
            if idx+1 <= len(key_list):
                months.append(month)
                storage_charges.append(storage_dic[month][0])
                compute_charges.append(compute_dic[month][0])
                egress_charges.append(egress_dic[month][0])

        # Calculate the charge differences between months
        storage_charges = self.calculate_diffs(storage_charges)
        compute_charges = self.calculate_diffs(compute_charges)
        egress_charges = self.calculate_diffs(egress_charges)

        # Remove the last month from the month categories
        # That we are taking the 1st date from but not using
        months = months[:-1]

        # Convert months to strings e.g. "May 2022" for plotting
        converted_months = [
            (datetime.strptime(month, "%m-%Y").strftime('%b %Y'))
            for month in months
        ]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=converted_months,
            y=compute_charges,
            name='Compute',
            hovertemplate='<br>Month: %{x}<br>Charge: $%{y:.2f}<br>'
                '<extra></extra>',
            marker=dict(color='#636EFA')
            )
        )

        fig.add_trace(go.Bar(
            x=converted_months,
            y=storage_charges,
            name='Storage',
            hovertemplate='<br>Month: %{x}<br>Charge: $%{y:.2f}<br>'
                '<extra></extra>',
            marker=dict(color='#EF553B')
            )
        )

        fig.add_trace(go.Bar(
            x=converted_months,
            y=egress_charges,
            name='Egress',
            hovertemplate='<br>Month: %{x}<br>Charge: $%{y:.2f}<br>'
                '<extra></extra>',
            marker=dict(color="#00CC96")
            )
        )

        fig.update_layout(
            title={
                'text': "Monthly Running Charges",
                'xanchor': 'center',
                'x': 0.5,
                'font_size': 18
            },
            xaxis_title="Month",
            xaxis_tickformat='%d %b %y',
            yaxis_title="Monthly estimated charge ($)",
            yaxis_tickformat=",d",
            width=1200,
            height=600,
            font_family='Helvetica',
        )

        # Add black border to bars
        fig.update_traces(
            marker_line_color = 'rgb(0,0,0)',
            marker_line_width = 1,
        )

        chart = fig.to_html()

        return chart


class StoragePlotFunctions():
    """Class for all of the storage plotting functions"""
    def __init__(self) -> None:
        self.current_year = dx_queries.no_of_days_in_month()[0].split('-')[0]
        self.today_date = dx_queries.no_of_days_in_month()[0]
        self.four_months_ago = date.today() + relativedelta(months=-4)
        self.start_of_four_months_ago = self.four_months_ago.replace(day=1)
        self.start_of_next_month = (
            date.today() + relativedelta(months=+1)
        ).replace(day=1)

        # Get Plotly discrete colour lists
        self.project_colours = px.colors.qualitative.Set1
        self.assay_colours = px.colors.qualitative.Bold
        # Specify colours for specific types of projects or assays
        # So don't change on diff numbers of types/assays during filtering
        self.proj_colour_dict = settings.PROJ_COLOUR_DICT
        self.assay_colour_dict = settings.ASSAY_COLOUR_DICT

        # Get all storage objects as queryset so multiple queries not needed
        self.storage_objects = StorageCosts.objects.all()

        self.total_live = self.get_todays_total_unique_size()[0]
        self.total_archived = self.get_todays_total_unique_size()[1]

        # Chart data which is shared by all plots
        self.chart_data = {
            'chart': {
                'type': 'column',
                'width': 1200,
                'height': 500,
                'style': {
                    'float': 'center'
                }
            },
            'title': {
                'text': 'Monthly Storage Cost'
            },
            'xAxis': {
                'categories': "",
                'labels': {
                    'style': {
                        'fontSize': '12px'
                    }
                }
            },
            'yAxis': {
                'allowDecimals': 'false',
                'min': '0',
                'title': {
                    'text': 'Total estimated storage cost ($)',
                    'style': {
                        'fontSize': '15px'
                    }
                },
                'stackLabels': {
                    'enabled': 'true',
                    'allowOverlap': 'true',
                    'style': {
                        'color': 'gray',
                        'textOutline': 0
                    },
                    'format': "{stack}"
                }
            },
            'setOptions': {
                'lang': {
                    'thousandsSep': ',',
                    'noData': 'No data to display'
                }
            },
            'plotOptions': {
                'column': {
                    'stacking': 'normal'
                    }
            },
            'exporting': {
                'buttons': {
                    'contextButton': {
                        'menuItems': [
                            "viewFullscreen", "printChart", "downloadPNG",
                            "downloadJPEG", "downloadPDF"
                        ]
                    }
                }
            },
            'series': "",
            "tooltip":{
                "pointFormat": "{series.name}: <b>${point.y:.2f}"
                "</b><br>{series.options.stack}<br>"
            }
        }

    def str_to_list(self, string):
        """
        Converts the entered to string to a list of proj or assay types

        Parameters
        ----------
        string :  str
            string of types enterered by user

        Returns
        -------
        string.strip(',').replace(' ', '').split(',') : list
            list stripped of whitespace + trailing commas
            split on internal commas
        e.g.
        strip_list(',001, 002, 003,')
            >> ['001', '002', '003']
        """
        return string.strip(',').replace(' ', '').split(',')
    
    def get_month_years_as_str(self, cost_list):
        """
        Converts a list of month years to stringified month-years

        Parameters
        ----------
        cost_list : Django query set as a list of dicts
        e.g. test =
        [{
            'date__date__month': 5,
            'date__date__year': 2022,
            'Live': 25.459,
            'Archived': 0.2379
        },
        {
            'date__date__month': 6,
            'date__date__year': 2022,
            'Live': 2.619,
            'Archived': 0.02458
        }]

        Returns
        -------
        string_months : list
            list of months in more readable form for plots
        e.g.
        get_month_years_as_str(test)
            >> ['May 2022', 'June 2022']
        """
        months = [(str(
            entry.get('date__date__month')), str(entry.get('date__date__year')
        )) for entry in cost_list
        ]

        converted_months = [(
            calendar.month_name[int(month_tuple[0])], month_tuple[1]
        ) for month_tuple in months
        ]

        string_months = list(map(" ".join, converted_months))

        return string_months

    def get_todays_total_unique_size(self):
        """
        Gets today's unique total (live/archived) for all files in all projects

        Parameters
        ----------
        None

        Returns
        -------
        live_total : float
            total size in GiB of all the live files in DNAnexus
        archived_total : float
            total size in GiB of all the archived files in DNAnexus
        """
        todays_total = StorageCosts.objects.filter(
            date__date=self.today_date
        ).aggregate(
            Live=Sum('unique_size_live'),
            Archived=Sum('unique_size_archived')
        )
        # If DNANexus has been queried, convert bytes to GiB
        # Otherwise set both to zero
        if todays_total.get('Live'):
            live_total = round(todays_total.get('Live') / (2**30), 2)
            archived_total = round(todays_total.get('Archived') / (2**30), 2)
        else:
            live_total = 0.0
            archived_total = 0.0

        return f"{live_total:,}", f"{archived_total:,}"

    def convert_to_df(self, category_chart_data):
        """
        Convert chart data to a pandas df then convert it to HTML
        So it can be shown below the graph and be easily exported

        Parameters
        ----------
        category_chart_data : dict
            dictionary which has all the chart attributes and data

        Returns
        -------
        chart_data : pd.DataFrame as HTML table
            the dataframe with Month, Type, State and Monthly Storage Cost
        """
        series_data = category_chart_data['series'].copy()
        months = category_chart_data['xAxis']['categories'].copy()

        # As data column value contains a list, expand this over multiple rows
        # Explode fills in the relevant data for those extra rows
        exploded = pd.json_normalize(data = series_data).explode('data')

        # If data exists, expand the months table according to the df length
        # So the correct month can be added to the right row
        if months:
            months = months * (int(len(exploded) / len(months)))
            exploded['Month'] = months
        # If no months exist (no data), keep months as empty list
        else:
            months = []

        # Re-order columns
        exploded = exploded.reindex(
            columns=[
                'Month', 'name', 'stack', 'data'
            ]
        )
        exploded.rename(
            columns={
                "name": "Type",
                "stack": "State",
                'data': 'Monthly storage cost ($)'
            },
            inplace = True
        )
        # Convert to HTML to easily show with DataTables
        chart_data = exploded.to_html(
            index=False,
            classes='table table-striped"',
            justify='left'
        )

        return chart_data


    def month_range_assay_type_and_proj_type(
        self, project_type, assay_type, month_start, month_end, form
    ):
        """
        Sets context when one project type and one assay type searched for

        Parameters
        ----------
        project_type :  str
            string that the project name begins with
        assay_type : str
            string that the project name ends with
        month_start : str
            first date of month to filter as start of range
        month_end : str
            last date of month to filter as end of range
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'storage_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """

        category_data_source = []
        # Default shows last 6 months
        # Filter by startswith project type and ends with assay type
        # Group by all available months
        # Sum by live vs archived
        cost_list = self.storage_objects.filter(
            date__date__range=[month_start, month_end],
            project__name__startswith=project_type,
            project__name__endswith=assay_type
            ).order_by().values(
                'date__date__month',
                'date__date__year'
                ).annotate(
                    Live=Sum('unique_cost_live'),
                    Archived=Sum('unique_cost_archived')
        )

        string_months = self.get_month_years_as_str(cost_list)

        # Set name of series
        # Get live values as list
        # Colour with dict or if proj type not in dict
        # Get colour from project_colours
        live_data = {
            'name': f"{project_type}*{assay_type}",
            'data': list(
                cost_list.values_list(
                    'Live', flat=True
                    )
            ),
            'stack': 'Live',
            'color': self.proj_colour_dict.get(
                project_type, self.project_colours[0]
            )
        }

        # linkedTo means it is linked to live
        # Change opacity to slightly differentiate live vs archived
        archived_data = {
                'name': f"{project_type}*{assay_type}",
                'data': list(
                    cost_list.values_list(
                        'Archived', flat=True
                    )
                ),
                'stack': 'Archived',
                'linkedTo': ':previous',
                'color': self.proj_colour_dict.get(
                    project_type, self.project_colours[0]
                ),
                'opacity': 0.8
        }

        category_data_source.append(live_data)
        category_data_source.append(archived_data)

        # Stacked grouped bar chart
        # Set categories to the stringified months present in the db
        # StackLabels format sets Live or Archived above bar
        # noData sets what to display when data == []
        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = string_months
        category_chart_data['series'] = category_data_source

        chart_data = self.convert_to_df(category_chart_data)

        context = {
            'storage_data': json.dumps(category_chart_data),
            'storage_df': chart_data,
            'form': form,
            'live_total': self.total_live,
            'archived_total': self.total_archived
        }

        return context

    def month_range_only_project_types(
        self, proj_types, month_start, month_end, form
    ):
        """
        Sets context when only project type(s) searched for

        Parameters
        ----------
        proj_types :  list
            list of project types searched for e.g. ['001','002','003']
        month_start : str
            first date of month to filter as start of range
        month_end : str
            last date of month to filter as end of range
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'storage_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # Filter by 'startswith' for each searched project type
        # For each proj add data to dict
        category_data_source = []
        count = -1
        for proj_type in proj_types:
            count += 1
            cost_list = self.storage_objects.filter(
                date__date__range=[month_start, month_end],
                project__name__startswith=proj_type,
            ).order_by().values(
                'date__date__month',
                'date__date__year'
                ).annotate(
                    Live=Sum('unique_cost_live'),
                    Archived=Sum('unique_cost_archived')
            )

            string_months = self.get_month_years_as_str(cost_list)

            # Get bar colour from dict or iterate over project_colours
            live_data = {
                'name': proj_type,
                'data': list(
                    cost_list.values_list(
                        'Live', flat=True
                    )
                ),
                'stack': 'Live',
                'color': self.proj_colour_dict.get(
                    proj_type, self.project_colours[count]
                )
            }

            archived_data = {
                'name': proj_type,
                'data': list(
                    cost_list.values_list(
                        'Archived', flat=True
                    )
                ),
                'stack': 'Archived',
                'linkedTo': ':previous',
                'color': self.proj_colour_dict.get(
                    proj_type, self.project_colours[count]
                ),
                'opacity': 0.8
            }

            category_data_source.append(live_data)
            category_data_source.append(archived_data)

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = string_months
        category_chart_data['series'] = category_data_source

        chart_data = self.convert_to_df(category_chart_data)

        context = {
            'storage_data': json.dumps(category_chart_data),
            'storage_df': chart_data,
            'form': form,
            'live_total': self.total_live,
            'archived_total': self.total_archived
        }

        return context

    def month_range_only_assay_types(
        self, assay_types, month_start, month_end, form
    ):
        """
        Sets context when only assay type(s) entered

        Parameters
        ----------
        assay_types :  list
            list of assay types searched for e.g. ['CEN','TWE','TSO500']
        month_start : str
            first date of month to filter as start of range
        month_end : str
            last date of month to filter as end of range
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'storage_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        category_data_source = []
        # Filter by 'endswith' for each searched assay type
        count = -1
        for assay_type in assay_types:
            count += 1
            cost_list = self.storage_objects.filter(
                date__date__range=[month_start, month_end],
                project__name__endswith=assay_type,
                ).order_by().values(
                    'date__date__month',
                    'date__date__year'
                    ).annotate(
                        Live=Sum('unique_cost_live'),
                        Archived=Sum('unique_cost_archived')
                    )

            string_months = self.get_month_years_as_str(cost_list)

            live_data = {
                'name': assay_type,
                'data': list(
                    cost_list.values_list(
                        'Live', flat=True
                    )
                ),
                'stack': 'Live',
                'color': self.assay_colour_dict.get(
                    assay_type, self.assay_colours[count]
                )
            }

            archived_data = {
                'name': assay_type,
                'data': list(
                    cost_list.values_list(
                        'Archived', flat=True
                    )
                ),
                'stack': 'Archived',
                'linkedTo': ':previous',
                'color': self.assay_colour_dict.get(
                    assay_type, self.assay_colours[count]
                ),
                'opacity': 0.8
            }

            category_data_source.append(live_data)
            category_data_source.append(archived_data)

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = string_months
        category_chart_data['series'] = category_data_source

        chart_data = self.convert_to_df(category_chart_data)

        context = {
            'storage_data': json.dumps(category_chart_data),
            'storage_df': chart_data,
            'form': form,
            'live_total': self.total_live,
            'archived_total': self.total_archived
        }

        return context

    def month_range_form_submitted_no_proj_or_assay(
        self, month_start, month_end, form
    ):
        """
        Sets context when 'All' months selected
        But no project types or assay types (only year + month)

        Parameters
        ----------
        month_start : str
            first date of month to filter as start of range
        month_end : str
            last date of month to filter as end of range
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'storage_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        storage_totals = self.storage_objects.filter(
            date__date__range=[month_start, month_end],
        ).order_by().values(
            'date__date__month',
            'date__date__year'
            ).annotate(
                Live=Sum('unique_cost_live'),
                Archived=Sum('unique_cost_archived')
            )

        string_months = self.get_month_years_as_str(storage_totals)

        # No need to loop over anything
        category_data_source = [
            {
                "name": "All projects",
                "data": list(storage_totals.values_list(
                    'Live', flat=True
                    )
                ),
                'stack': 'Live',
                'color': 'rgb(27,158,119)'
            },
            {
                "name": "All projects",
                "data": list(storage_totals.values_list(
                    'Archived', flat=True
                    )
                ),
                'stack': 'Archived',
                'linkedTo': ':previous',
                'color': 'rgb(27,158,119)',
                'opacity': 0.8
            }
        ]

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = string_months
        category_chart_data['series'] = category_data_source

        chart_data = self.convert_to_df(category_chart_data)

        context = {
            'storage_data': json.dumps(category_chart_data),
            'storage_df': chart_data,
            'form': form,
            'live_total': self.total_live,
            'archived_total': self.total_archived
        }

        return context

    def form_is_not_submitted_or_invalid(self, form):
        """
        Sets context for the landing page where no form is submitted
        Or when the form is invalid
        i.e. >1 project type and >1 assay type are entered
        Sets graph to all projects for all months grouped by month

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'storage_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        storage_totals = self.storage_objects.filter(
            date__date__range=[
                self.start_of_four_months_ago, self.start_of_next_month
            ],
        ).order_by().values(
            'date__date__month',
            'date__date__year'
        ).annotate(
            Live=Sum('unique_cost_live'),
            Archived=Sum('unique_cost_archived')
        )

        string_months = self.get_month_years_as_str(storage_totals)

        category_data_source = [
            {
                "name": "All projects",
                "data": list(storage_totals.values_list(
                    'Live', flat=True
                        )
                    ),
                'stack': 'Live',
                'color': 'rgb(27,158,119)'
            },

            {
                "name": "All projects",
                "data": list(storage_totals.values_list(
                    'Archived', flat=True
                    )
                ),
                'stack': 'Archived',
                'linkedTo': ':previous',
                'color': 'rgb(27,158,119)',
                'opacity': 0.8
            }
        ]

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = string_months
        category_chart_data['series'] = category_data_source

        chart_data = self.convert_to_df(category_chart_data)

        context = {
                'storage_data': json.dumps(category_chart_data),
                'storage_df': chart_data,
                'form': form,
                'live_total': self.total_live,
                'archived_total': self.total_archived
        }

        return context
