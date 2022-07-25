"""This script holds plotting functions used in views.py"""

import calendar
import json
import pandas as pd
import plotly.express as px

from datetime import date
from dateutil.relativedelta import relativedelta

from dashboard.models import StorageCosts
from django.conf import settings
from django.db.models import Sum
from scripts import DNAnexus_queries as dx_queries

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
                },
                'chartOptions': {
                    'chart': {
                        'style': {
                            'fontFamily': 'Roboto'
                        }
                    }
                }
            },
            'series': "",
            "tooltip": {
                "pointFormat": "{series.name}: <b>${point.y:.2f}"
                "</b><br>{series.options.stack}<br>"
            }
        }

    def str_to_list(self, string):
        """
        Converts the entered string to a list of proj or assay types

        Parameters
        ----------
        string :  str
            string of types enterered by user

        Returns
        -------
        string.strip(',').replace(' ', '').split(',') : list
            list where the str is stripped of whitespace + trailing commas
            then split on internal commas
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
        months = [
            (
                str(entry.get('date__date__month')),
                str(entry.get('date__date__year'))
            ) for entry in cost_list
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
            total size in TiB of all the live files in DNAnexus
        archived_total : float
            total size in TiB of all the archived files in DNAnexus
        """
        todays_total = StorageCosts.objects.filter(
            date__date=self.today_date
        ).aggregate(
            Live=Sum('unique_size_live'),
            Archived=Sum('unique_size_archived')
        )
        # If DNANexus has been queried today, convert bytes to TiB
        # Otherwise set both to "not yet calculated"
        if todays_total.get('Live'):
            live_total = round(
                ((todays_total.get('Live') / (2**30))/1024), 2
            )
            formatted_live_total = f"{live_total:,.2f} TiB"
            archived_total = round(
                ((todays_total.get('Archived') / (2**30))/1024), 2
            )
            formatted_archived_total = f"{archived_total:,.2f} TiB"
        else:
            formatted_live_total = "Not yet calculated"
            formatted_archived_total = "Not yet calculated"

        return formatted_live_total, formatted_archived_total

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
        # Explode to fill in the relevant data for those extra rows
        exploded = pd.json_normalize(data=series_data).explode('data')

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
                "name": "Scope",
                "stack": "State",
                'data': 'Monthly storage cost ($)'
            },
            inplace=True
        )
        if exploded['Monthly storage cost ($)'].isnull().values.any():
            pass
        else:
            exploded[
                    'Monthly storage cost ($)'
                ] = exploded['Monthly storage cost ($)'].astype(float)

        # Convert to HTML to easily show with DataTables
        chart_data = exploded.to_html(
            index=False,
            classes='table table-striped"',
            justify='left',
            float_format="%.3f"
        )

        return chart_data

    def format_proj_level_table(self, proj_level_df):
        """
        Format the table containing project level data and return
        As HTML table to be used by DataTables

        Parameters
        ----------
        proj_level_df : pd.DataFrame
            dataframe created directly from Django queryset

        Returns
        -------
        formatted_html_proj_table : pd.DataFrame as HTML table
            formatted dataframe

        +---------------+-------------------+------------------+-----------+---------------+
        | project__name | date__date__month | date__date__year | Live_Cost | Archived_Cost |
        +---------------+-------------------+------------------+-----------+---------------+
        | proj-X        |                 7 |             2022 |    2.5880 |        0.0000 |
        | proj-Y        |                 6 |             2022 |    1.4752 |          0.00 |
        +---------------+-------------------+------------------+-----------+---------------+
                                |
                                ▼
        +---------+----------+---------------+-------------------+
        | Project |  Month   | Live Cost ($) | Archived Cost ($) |
        +---------+----------+---------------+-------------------+
        | proj-X  | Jul 2022 |         2.588 |             0.000 |
        | proj-Y  | Jun 2022 |         1.475 |              0.00 |
        +---------+----------+---------------+-------------------+
        """
        if proj_level_df.empty:
            proj_level_df = pd.DataFrame()

            formatted_html_proj_table = proj_level_df.to_html(
                index=False,
                classes='table table-striped"',
                justify='left',
            )

        else:
            # Convert int month to str calendar month
            proj_level_df['date__date__month'] = proj_level_df[
                'date__date__month'
            ].apply(lambda x: calendar.month_abbr[x])

            # Change year to str so can concatenate
            proj_level_df["date__date__year"] = proj_level_df[
                'date__date__year'
            ].astype(str)

            # Merge the two month + year columns as new col
            proj_level_df["Month"] = proj_level_df[
                "date__date__month"
            ] + " " + proj_level_df["date__date__year"]

            # Subset df
            proj_level_df = proj_level_df[
                [
                    'project__name', 'Month',
                    'Live_Cost', 'Archived_Cost'
                ]
            ]

            proj_level_df.rename(
                columns={
                    'project__name': 'Project',
                    'Live_Cost': 'Live Cost ($)',
                    'Archived_Cost': 'Archived Cost ($)'
                }, inplace=True
            )

            formatted_html_proj_table = proj_level_df.to_html(
                index=False,
                classes='table table-striped"',
                justify='left',
                float_format="%.3f"
            )

        return formatted_html_proj_table

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
            'storage_df' : pd.DataFrame of the data which makes up the chart
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

        proj_level_qs = pd.DataFrame.from_records(
            StorageCosts.objects.filter(
                date__date__range=[month_start, month_end],
                project__name__startswith=project_type,
                project__name__endswith=assay_type
            ).order_by().values(
                'project__name',
                'date__date__month',
                'date__date__year'
            ).annotate(
                Live_Cost=Sum('unique_cost_live'),
                Archived_Cost=Sum('unique_cost_archived')
            )
        )

        proj_level_df = self.format_proj_level_table(proj_level_qs)

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = string_months
        category_chart_data['series'] = category_data_source

        chart_data = self.convert_to_df(category_chart_data)

        context = {
            'storage_data': json.dumps(category_chart_data),
            'storage_df': chart_data,
            'form': form,
            'proj_level_df': proj_level_df
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
        proj_level_df = pd.DataFrame()
        category_data_source = []

        for count, proj_type in enumerate(proj_types):
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
                'name': f"{proj_type}*",
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
                'name': f"{proj_type}*",
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

            # Make project level df
            cost_list = pd.DataFrame.from_records(
                StorageCosts.objects.filter(
                    date__date__range=[month_start, month_end],
                    project__name__startswith=proj_type
                ).order_by().values(
                    'project__name',
                    'date__date__month',
                    'date__date__year'
                ).annotate(
                    Live_Cost=Sum('unique_cost_live'),
                    Archived_Cost=Sum('unique_cost_archived')
                )
            )

            proj_level_df = pd.concat([proj_level_df, cost_list])

        proj_level_df = self.format_proj_level_table(proj_level_df)

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = string_months
        category_chart_data['series'] = category_data_source

        chart_data = self.convert_to_df(category_chart_data)

        context = {
            'storage_data': json.dumps(category_chart_data),
            'storage_df': chart_data,
            'form': form,
            'proj_level_df': proj_level_df
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
        proj_level_df = pd.DataFrame()
        category_data_source = []
        # Filter by 'endswith' for each searched assay type
        for count, assay_type in enumerate(assay_types):
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
                'name': f"*{assay_type}",
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
                'name': f"*{assay_type}",
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

            # Make project level df
            cost_list = pd.DataFrame.from_records(
                StorageCosts.objects.filter(
                    date__date__range=[month_start, month_end],
                    project__name__endswith=assay_type
                ).order_by().values(
                    'project__name',
                    'date__date__month',
                    'date__date__year'
                ).annotate(
                    Live_Cost=Sum('unique_cost_live'),
                    Archived_Cost=Sum('unique_cost_archived')
                )
            )

            proj_level_df = pd.concat([proj_level_df, cost_list])

        proj_level_df = self.format_proj_level_table(proj_level_df)

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = string_months
        category_chart_data['series'] = category_data_source

        chart_data = self.convert_to_df(category_chart_data)

        context = {
            'storage_data': json.dumps(category_chart_data),
            'storage_df': chart_data,
            'form': form,
            'proj_level_df': proj_level_df
        }

        return context

    def all_projects_between_months(
        self, month_start, month_end, form
    ):
        """
        Sets context for all projects between certain months
        This is either specified by user or by default this
        Is set to last four months in views for the landing page
        Or where no form is submitted or form invalid

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
            'storage_df': pd.DataFrame of the data that makes up the chart
            'proj_level_df': pd.Dataframe the live + archived costs per project
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

        # Add project-level df
        proj_level_qs = pd.DataFrame.from_records(
            StorageCosts.objects.filter(
                date__date__range=[month_start, month_end]
            ).order_by().values(
                'project__name',
                'date__date__month',
                'date__date__year'
            ).annotate(
                Live_Cost=Sum('unique_cost_live'),
                Archived_Cost=Sum('unique_cost_archived')
            )
        )

        proj_level_df = self.format_proj_level_table(proj_level_qs)

        context = {
            'storage_data': json.dumps(category_chart_data),
            'storage_df': chart_data,
            'form': form,
            'proj_level_df': proj_level_df
        }

        return context
