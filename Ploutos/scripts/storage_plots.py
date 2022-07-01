"""This script holds plotting functions used in views.py"""

import calendar
import json
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

    def all_charge_types(self, totals):
        """
        Set context when all charge types are searched for
        Parameters
        ----------
        totals :  queryset
            queryset already filtered by the specified daterange

        Returns
        -------
        fig : Plotly figure object
        """

        # Plot the date and storage charges as line graph
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

        # Get the relevant info as a list
        storage_charges, compute_charges, egress_charges = zip(*charges)

        # Calculate one date charges minus previous date
        storage_charge_diff = self.calculate_diffs(storage_charges)
        compute_charge_diff = self.calculate_diffs(compute_charges)
        egress_charge_diff = self.calculate_diffs(egress_charges)

        fig = go.Figure(layout={'hovermode': 'x unified'})

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

    def specific_charge_type(self, totals, charge_type):
        """
        Set context when a specific charge types is searched for
        Parameters
        ----------
        totals :  queryset
            queryset already filtered by the specified daterange
        charge_type : str
            the charge type the user wants to see e.g. 'Egress'

        Returns
        -------
        fig : Plotly figure object
        """
        # Plot the date and storage charges as line graph
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

        # Get relevant charge from tuples
        storage_charges, compute_charges, egress_charges = zip(*charges)

        # Calculate charge relative to previous day
        storage_charge_diff = self.calculate_diffs(storage_charges)
        compute_charge_diff = self.calculate_diffs(compute_charges)
        egress_charge_diff = self.calculate_diffs(egress_charges)

        charge_dict = {
            "Egress": {
                "colour": "#00CC96",
                "data": egress_charge_diff,
                "title": "Egress Daily Running Charges"
            },
            "Compute": {
                "colour": '#636EFA',
                "data": compute_charge_diff,
                "title": "Compute Daily Running Charges"
            },
            "Storage": {
                "colour": '#EF553B',
                "data": storage_charge_diff,
                "title": "Storage Daily Running Charges"
            }
        }

        fig = go.Figure(layout={'hovermode': 'x unified'})

        fig.add_trace(go.Bar(
            x=stringified_dates,
            y=charge_dict[charge_type]["data"],
            name='Compute',
            marker=dict(color=charge_dict[charge_type]["colour"]),
            hovertemplate='%{y:.2f}'
            )
        )

        fig.update_layout(
            title={
                'text': charge_dict[charge_type]["title"],
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

        fig.data[0].name = f"{charge_type}"
        fig.update_traces(
            marker_line_color = 'rgb(0,0,0)',
            marker_line_width = 1,
            showlegend=True
        )

        return fig


    def form_not_submitted_or_invalid(self):
        """
        Set context when the form is not submitted
        Or when the form is not valid (wrong dates)
        Includes all dates present in db and all charge types
        Parameters
        ----------
        form : Django form object
            form either as Form(request.GET) or Form()
        Returns
        -------
        context : dict
            context to pass to HTML

        """
        totals = DailyOrgRunningTotal.objects.filter(
            date__date__range=[str(self.four_months_ago), self.today_date]
        )

        # Plot the date and storage charges as line graph
        charges = totals.order_by(
            'date__date'
        ).values_list(
            'storage_charges', 'compute_charges', 'egress_charges'
        )

        # Get dates in order from the db
        dates = totals.order_by(
            'date__date'
        ).values_list(
            'date__date', flat=True
        )

        # Convert dates to strs, remove last date
        stringified_dates = [str(date) for date in dates][:-1]

        # Get relevant charge from tuples
        storage_charges, compute_charges, egress_charges = zip(*charges)

        # Calculate charge for the day relative to previous day
        storage_charge_diff = self.calculate_diffs(storage_charges)
        compute_charge_diff = self.calculate_diffs(compute_charges)
        egress_charge_diff = self.calculate_diffs(egress_charges)

        fig = go.Figure(layout={'hovermode': 'x unified'})

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

        fig.update_traces(
            marker_line_color = 'rgb(0,0,0)',
            marker_line_width = 1
        )

        chart = fig.to_html()

        return chart

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
        monthly_charges = DailyOrgRunningTotal.objects.filter(
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

        storage_dic = defaultdict(list)
        compute_dic = defaultdict(list)
        egress_dic = defaultdict(list)
        months = []
        storage_charges = []
        compute_charges = []
        egress_charges = []

        # Make each a defaultdict e.g. {'5-2022': [500.20, 100.40]}
        for item in monthly_charges:
            storage_dic[f"{item[0]}-{item[1]}"].append(item[2])
            compute_dic[f"{item[0]}-{item[1]}"].append(item[3])
            egress_dic[f"{item[0]}-{item[1]}"].append(item[4])

        # Get the keys and sort by month-year
        # Only need to do this for storage_dic as all have same keys
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
            y=storage_charges,
            name='Storage',
            hovertemplate='<br>Month: %{x}<br>Charge: $%{y:.2f}<br>'
                '<extra></extra>',
            marker=dict(color='#EF553B')
            )
        )

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
                'font_size': 24
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
        self.six_months_ago = date.today() + relativedelta(months=-6)
        self.start_of_six_months_ago = self.six_months_ago.replace(day=1)
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
                        'fontWeight': 'bold',
                        'color': 'gray'
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
        cost_list = StorageCosts.objects.filter(
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

        context = {
            'storage_data': json.dumps(category_chart_data),
            'form': form
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
            cost_list = StorageCosts.objects.filter(
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

        context = {
            'storage_data': json.dumps(category_chart_data),
            'form': form
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
            cost_list = StorageCosts.objects.filter(
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

        context = {
            'storage_data': json.dumps(category_chart_data),
            'form': form
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
        storage_totals = StorageCosts.objects.filter(
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

        context = {
            'storage_data': json.dumps(category_chart_data),
            'form': form
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
        storage_totals = StorageCosts.objects.filter(
            date__date__range=[
                self.start_of_six_months_ago, self.start_of_next_month
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

        context = {
                'storage_data': json.dumps(category_chart_data),
                'form': form
        }

        return context
