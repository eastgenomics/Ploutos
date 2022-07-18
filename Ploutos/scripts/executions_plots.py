"""
This script holds plotting functions for visualising
jobs and analyses (executions) used in views.py
"""

import json
import plotly.express as px
import plotly.graph_objects as pgo
from datetime import date

from dashboard.models import ComputeCosts, Dates, Executables, Projects, StorageCosts
from django.conf import settings
from django.db.models import Func, F, Sum, IntegerField
from scripts import DNAnexus_queries as dx_queries
from scripts import date_conversion as dc
import pandas as pd

class ExecutionPlotFunctions():
    """
    Class of plotting functions for executions graph.
    """

    def __init__(self) -> None:
        self.current_year = dx_queries.no_of_days_in_month()[0].split('-')[0]
        # Get Plotly discrete colour lists
        self.project_colours = px.colors.qualitative.Set1
        self.assay_colours = px.colors.qualitative.Bold
        # Specify colours for specific types of projects or assays
        # So don't change on diff numbers of types/assays during filtering
        self.proj_colour_dict = settings.PROJ_COLOUR_DICT
        self.assay_colour_dict = settings.ASSAY_COLOUR_DICT
        # Find months from db as categories for the graph as list
        self.month_categories = list(
            ComputeCosts.objects.order_by().values_list(
                'date__date__month', flat=True
                ).distinct()
            )
        self.day_categories = list(
            ComputeCosts.objects.order_by().values_list(
                'date__date', flat=True
                ).distinct()
            )
        # Convert the integer months present in the db to strings
        # Importing the date conversion dict because for some reason Python
        # Wouldn't find it even though it's literally defined above ?
        self.string_months = [
            month if month not in dc.date_conversion_dict
            else dc.date_conversion_dict[month] for month
            in self.month_categories
        ]

        # Chart data which is shared by all plots
        self.time_chart_data = {
            'chart': {
                'zoomType': 'x',
                'type': 'column',
                'width': 1200,
                'height': 500,
                'style': {
                    'float': 'center'
                }
            },
            'title': {
                'text': 'Compute Costs'
            },
            'xAxis': {
                'type': 'datetime',
                'dateTimeLabelFormats': {
                    'month': '%e. %b',
                    'year': '%b'
                },
                'tickInterval': 24 * 3600 * 1000,
                'tickWidth': 1,
                'minPadding': 0.5,
                'maxPadding': 0.5
            },
            'yAxis': {
                'allowDecimals': 'false',
                'min': '0',
                'title': {
                    'text': 'Daily compute cost ($)'
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
                },
                'useUTC': False,
            },
            'plotOptions': {
                'series': {
                    'stacking': 'normal'
                }
            },
            'series': []
        }
        # Chart data which is shared by all plots
        self.bar_chart_data = {
            'chart': {
                'type': 'column',
                'width': 1200,
                'height': 500,
                'style': {
                    'float': 'center'
                }
            },
            'title': {
                'text': 'Compute Costs'
            },
            'xAxis': {
                'categories': ""
            },
            'yAxis': {
                'allowDecimals': 'false',
                'min': '0',
                'title': {
                    'text': 'Monthly compute cost ($)'
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
            'series': ""
        }

        # Chart data which is shared by all plots without stacking
        self.bar_chart_nostack_data = {
            'chart': {
                'type': 'column',
                'width': 1200,
                'height': 500,
                'style': {
                    'float': 'center'
                }
            },
            'title': {
                'text': 'Compute Costs'
            },
            'xAxis': {
                'categories': ""
            },
            'yAxis': {
                'allowDecimals': 'false',
                'min': '0',
                'title': {
                    'text': 'Monthly compute cost ($)'
                },
            },
            'setOptions': {
                'lang': {
                    'thousandsSep': ',',
                    'noData': 'No data to display'
                }
            },
            'series': ""
        }


    def str_to_list(self, string):
        """
        Strips

        Parameters
        ----------
        list_to_strip :  str
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


    def all_months_default(self, form):
        """
        Default graph when 'All' months selected
        """

        # Get all compute costs for the year

        category_data_source = []
        # project_types = ["001", "002", "003", "004"]
        year = str(date.today().year)
        cost_list = ComputeCosts.objects.filter(
            # project__name__startswith=project_types,
            date__date__year=year
        ).order_by().values(
            'date__date__month'
        ).annotate(
            cost_summed=Sum('total_cost'),
        )

        data = {
                'name': f"General Trends {year}",
                'data': list(
                    cost_list.values_list(
                        'total_cost', flat=True
                        )
                ),
                'stack': 'total_cost',
            }

        category_data_source.append(data)
        category_chart_data = self.bar_chart_data.copy()
        category_chart_data['xAxis']['categories'] = self.string_months
        category_chart_data['series'] = category_data_source

        # category_chart_data = {
        #         'chart': {'type': 'pie'},
        #         'title': {'text': "All Executions Totals"},
        #         'setOptions': {
        #             'lang': {
        #                 'thousandsSep': ','
        #             }
        #         },
        #         'accessibility': {
        #             'announceNewData': {
        #                 'enabled': True
        #             }
        #         },
        #         'plotOptions': {
        #             'series': {
        #                 'dataLabels': {
        #                     'enabled': True,
        #                     'format': '{point.name}: <br>{point.percentage:.1f} %<br>total: {point.y}',
        #                     'padding': 0,
        #                     'style': {
        #                         'fontSize': '10px'
        #                     }
        #                 }
        #             }
        #         },
        #         'tooltip': {
        #             'headerFormat': '<span style="font-size:11px; color:#8e5ea2">{series.name}<br>{point.percentage:.1f} %'
        #                             '</span><br>',
        #             'pointFormat': '<span style="color:#3cba9f">{point.name}</span>: <b>{point.y}</b><br/>'

        #         },
        #         'series': [category_data_source],
        #         }

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df(category_chart_data)

        return json_chart_data, chart_df



    def daily_month_range_all_project_types(self, form):
        # Filter by 'startswith' for each searched project type
        # For each proj add data to dict
        category_data_source = []
        count = -1
        project_types = ['001', '002', '003', '004']
        current_year = date.today().year
        # appended_list = []
        for proj_type in project_types:
            count += 1
            cost_list = ComputeCosts.objects.filter(
                project__name__startswith=proj_type,
                date__date__year=year
            ).order_by().values(
                'date__date').annotate(total_cost=Sum('total_cost'))
            cost_dates = cost_list.annotate(date_unix=Func(F('date__date'),
                                            function='UNIX_TIMESTAMP',
                                            output_field=IntegerField())*1000)
            compute_data = {
                'name': proj_type,
                'data': list(
                    cost_dates.values_list('date_unix',
                                           'total_cost')),  # flat=True when on var.
                'color': self.proj_colour_dict.get(
                    proj_type, self.project_colours[0]
                    )
            }

            category_data_source.append(compute_data)
            category_chart_data = self.time_chart_data.copy()
            category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df(category_chart_data)

        return json_chart_data, chart_df


    def daily_last_4_months_all_byproject_types(self, project_types, form):
        """
        Sets context when no months selected with no projects specified.

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'compute_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # Filter by 'startswith' for each searched project type
        # For each proj add data to dict
        category_data_source = []
        count = -1
        #project_types = ['001', '002', '003', '004']
        year = str(date.today().year)  # year = str(date.today().year)
        # appended_list = []
        project_types = self.str_to_list(project_types)
        for proj_type in project_types:
            count += 1
            cost_list = ComputeCosts.objects.filter(
                project__name__startswith=proj_type,
                date__date__year=year
            ).order_by().values(
                'date__date').annotate(total_cost=Sum('total_cost'))
            cost_dates = cost_list.annotate(date_unix=Func(F('date__date'),
                                            function='UNIX_TIMESTAMP',
                                            output_field=IntegerField())*1000)
            compute_data = {
                'name': proj_type,
                'data': list(
                    cost_dates.values_list('date_unix',
                                           'total_cost')),  # flat=True when on var.
                'color': self.proj_colour_dict.get(
                    proj_type, self.project_colours[0]
                    )
            }

            category_data_source.append(compute_data)
            category_chart_data = self.time_chart_data.copy()
            category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_timeseries(project_types)

        return json_chart_data, chart_df


    def daily_last_4_months_all_byassay_types(self, assay_types, form):
        """
        Sets context when no months selected with no projects specified.

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'compute_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # Filter by 'startswith' for each searched project type
        # For each proj add data to dict

        category_data_source = []
        count = -1
        year = str(date.today().year)

        assay_types = self.str_to_list(assay_types)
        for assay_type in assay_types:
            count += 1
            cost_list = ComputeCosts.objects.filter(
                project__name__endswith=assay_type,
                date__date__year=year
            ).order_by().values(
                'date__date').annotate(total_cost=Sum('total_cost'))
            cost_dates = cost_list.annotate(date_unix=Func(F('date__date'),
                                            function='UNIX_TIMESTAMP',
                                            output_field=IntegerField())*1000)
            compute_data = {
                'name': assay_type,
                'data': list(
                    cost_dates.values_list('date_unix',
                                           'total_cost')),  # flat=True when on var.
                # 'color': self.assay_colour_dict.get(
                #     assay_type, self.assay_colours[0]
                #     )
            }

            category_data_source.append(compute_data)
            category_chart_data = self.time_chart_data.copy()
            category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_alldata_by_assay(assay_types)

        return json_chart_data, chart_df


    def daily_last_4_months_all_byproject_and_assay(self, project_types, assay_types, form):
        """
        Sets context when no months selected with no projects specified.

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'compute_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # Filter by 'startswith' for each searched project type
        # For each proj add data to dict

        category_data_source = []
        count = -1
        year = str(date.today().year)

        assay_types = self.str_to_list(assay_types)
        project_types = self.str_to_list(project_types)
        for proj_type in project_types:
            for assay_type in assay_types:
                count += 1
                cost_list = ComputeCosts.objects.filter(
                    project__name__startswith=proj_type,
                    project__name__endswith=assay_type,
                    date__date__year=year
                ).order_by().values(
                    'date__date').annotate(total_cost=Sum('total_cost'))
                cost_dates = cost_list.annotate(date_unix=Func(F('date__date'),
                                                function='UNIX_TIMESTAMP',
                                                output_field=IntegerField())*1000)
                compute_data = {
                    'name': f"{proj_type}-{assay_type}",
                    'data': list(
                        cost_dates.values_list('date_unix',
                                               'total_cost')),  # flat=True when on var.
                    # 'color': self.assay_colour_dict.get(
                    #     assay_type, self.assay_colours[0]
                    #     )
                }

                category_data_source.append(compute_data)
                category_chart_data = self.time_chart_data.copy()
                category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_alldata_byproject_assay(project_types,
                                                               assay_types)

        return json_chart_data, chart_df


    def all_months_only_project_types(self, project_types, form):
        """
        Sets context when no months selected with no projects specified.

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'compute_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # Filter by 'startswith' for each searched project type
        # For each proj add data to dict
        category_data_source = []
        count = -1
        # project_types = ['001', '002', '003', '004']
        year = str(date.today().year)  # year = str(date.today().year)
        # appended_list = []
        project_types = self.str_to_list(project_types)
        for proj_type in project_types:
            count += 1
            cost_list = ComputeCosts.objects.filter(
                project__name__startswith=proj_type,
                date__date__year=year
            ).order_by().values(
                'date__date').annotate(total_cost=Sum('total_cost'))
            cost_dates = cost_list.annotate(date_unix=Func(F('date__date'),
                                            function='UNIX_TIMESTAMP',
                                            output_field=IntegerField())*1000)
            compute_data = {
                'name': proj_type,
                'data': list(
                    cost_dates.values_list('date_unix',
                                           'total_cost')),  # flat=True when on var.
                'color': self.proj_colour_dict.get(
                    proj_type, self.project_colours[0]
                    )
            }

            category_data_source.append(compute_data)
            category_chart_data = self.time_chart_data.copy()
            category_chart_data['series'] = category_data_source

        context = {
            'compute_data': json.dumps(category_chart_data),
            'form': form
        }

        return context


    def specific_month_range_proj_and_assay(
            self, project_type, assay_type, year,
            month, converted_month, form
    ):
        """
        Sets context when specific month is selected
        With one project type and one assay type

        Parameters
        ----------
        project_type: str
            string that the project name starts with
        assay_type :  str
            string that the project name ends with
        year : str
            year that the date of the objects should belong to e.g. '2022'
        month : str
            month that the date of the objects should belong to e.g. '5'
        converted_month : str
            the specified month as a string e.g. "May"
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'compute_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        category_data_source = []
        # Proj name starts wth project type and ends with assay type
        # Filter for specific year and month
        cost_list = ComputeCosts.objects.filter(
            project__name__startswith=project_type,
            project__name__endswith=assay_type,
            date__date__year=year,
            date__date__month=month
            ).aggregate(
                Cost=Sum('total_cost')
            )

        # Get the Cost aggregate for those projects
        # If QS empty, returns None which affects noData message
        # Keep as list with actual data or convert [None] to []
        Cost = cost_list.get('Cost')
        if Cost:
            Cost = [Cost]
        else:
            Cost = []

        Cost_data = {
            'name': f"{project_type}*{assay_type}",
            'data': Cost,
            'stack': 'Cost',
            'color': self.proj_colour_dict.get(
                project_type, self.project_colours[0]
            )
        }

        category_data_source.append(Cost_data)

        # As only one series, categories must be a list
        # Or Highcharts bug means it
        # Only shows the first letter of the category
        category_chart_data = self.bar_chart_data.copy()
        category_chart_data['xAxis']['categories'] = [converted_month]
        category_chart_data['series'] = category_data_source

        context = {
            'compute_data': json.dumps(category_chart_data),
            'form': form
        }

        return context


    def all_months_only_proj_assay_types(self, project_types, assay_types, form):
        """
        Sets context when 'All' months selected, with only assay type(s)
        Parameters
        ----------
        assay_types :  list
            list of assay types searched for e.g. ['CEN','TWE','TSO500']
        year : str
            year that the date of the objects should belong to
        form : Django form object
            the related Django form in forms.py
        Returns
        -------
        context : dict
            'compute_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        category_data_source = []
        # Filter by 'endswith' for each searched assay type
        year = str(date.today().year)
        project_types = self.str_to_list(project_types)
        cost_list = ComputeCosts.objects.filter(
            project__name__startswith=project_types,
            project__name__endswith=assay_types,
            date__date__year=year
            ).order_by().values(
                'date__date__month')
        compute_data = {
            'name': f"{project_types}*{assay_types}",
            'data': list(
                cost_list.values_list(flat=True)
            ),
            'stack': 'total_cost',  # live #Compute
            # 'color': self.assay_colour_dict.get(
            #     project_types, self.assay_colours[0]
            # ),
            'opacity': 0.8
        }

        category_data_source.append(compute_data)

        category_chart_data = self.bar_chart_data.copy()
        category_chart_data['xAxis']['categories'] = self.string_months
        category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df(category_chart_data)

        return json_chart_data, chart_df


    def monthly_byproject(self, project_types, form):
        """Graph showing monthly total cost by projects (startswith filter)"""

        # Get all compute costs for the year
        project_types = self.str_to_list(project_types)
        category_data_source = []
        year = str(date.today().year)

        for project_type in project_types:
            cost_list = ComputeCosts.objects.filter(
                project__name__startswith=project_type,
                date__date__year=year
            ).order_by().values(
                'date__date__month'
            ).annotate(
                total_cost=Sum('total_cost'),
            )

            data = {
                'name': f"{project_type}",
                'data': list(
                    cost_list.values_list(
                        'total_cost', flat=True
                        )
                ),
                'color': self.proj_colour_dict.get(
                    project_type, self.project_colours[0]
                    )
                }

            category_data_source.append(data)
        category_chart_data = self.bar_chart_nostack_data.copy()
        category_chart_data['xAxis']['categories'] = self.string_months
        category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_projectonly(category_chart_data)

        return json_chart_data, chart_df



    def monthly_byassay(self, assay_types, form):
        """Graph showing monthly total cost by projects (startswith filter)"""

        # Get all compute costs for the year
        assay_types = self.str_to_list(assay_types)
        category_data_source = []
        year = str(date.today().year)

        for assay_type in assay_types:
            cost_list = ComputeCosts.objects.filter(
                project__name__endswith=assay_type,
                date__date__year=year
            ).order_by().values(
                'date__date__month'
            ).annotate(
                total_cost=Sum('total_cost'),
            )

            data = {
                'name': f"{assay_type}",
                'data': list(
                    cost_list.values_list(
                        'total_cost', flat=True
                        )
                ),
                # 'color': self.assay_colour_dict.get(
                #     assay_type, self.assay_colours[0]
                #     )
                }

            category_data_source.append(data)
        category_chart_data = self.bar_chart_nostack_data.copy()
        category_chart_data['xAxis']['categories'] = self.string_months
        category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_assayonly(category_chart_data)

        return json_chart_data, chart_df


    def monthly_byproject_assays_stacked(self, project_types, assay_types, form):
        """All months filtered by project type and stacked by assay"""

        # Set the graph dictionary
        grouped_stacked_chart = {
            'chart': {
                'type': 'column',
                'width': 1200,
                'height': 500,
                'style': {
                    'float': 'center'
                }
            },

            'title': {
                'text': 'Total costs ($), grouped by project type'
            },

            'xAxis': {
                'categories': ""
            },

            'yAxis': {
                'allowDecimals': False,
                'min': 0,
                'title': {
                    'text': 'Total costs ($)'
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

            'series': []
            }

        #Get all compute costs for the year
        category_data_source = []
        year = str(date.today().year)
        project_types = self.str_to_list(project_types)
        assay_types = self.str_to_list(assay_types)

        for project_type in project_types:
            for assay_type in assay_types:
                cost_list = ComputeCosts.objects.filter(
                    project__name__startswith=project_type,
                    project__name__endswith=assay_type,
                    date__date__year=year
                ).order_by().values(
                    'date__date__month'
                ).annotate(
                    total_cost=Sum('total_cost'),
                )

                data = {
                    'name': f"{project_type}-{assay_type}",
                    'data': list(
                        cost_list.values_list(
                            'total_cost', flat=True,
                            )
                    ),
                    # 'color': self.proj_colour_dict.get(
                    #     project_type, self.project_colours[0]
                    #     ),
                    'stack': f'{project_type}'
                    }

                category_data_source.append(data)
        category_chart_data = grouped_stacked_chart
        # categories = []
        # project_types = [x for x in project_types]
        # for proj in project_types:
        #     categories.append({"name": f"{proj}",
        #                        "categories": self.string_months})
        # # for month in self.string_months:
        #     categories.append({"name": f"{month}",
        #                        "categories": project_types})
        category_chart_data['xAxis']['categories'] = self.string_months
        category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_alldata_byproject_assay(project_types,
                                                              assay_types)

        return json_chart_data, chart_df



    def months_default_totals_redundant(self, form):
        """Default graph when 'All' months selected"""

        # Get all compute costs for the year

        category_data_source = []
        year = str(date.today().year)

        for project_type in project_types:
            cost_list = ComputeCosts.objects.filter(
                date__date__year=year
            ).order_by().values(
                'date__date__month'
            ).annotate(
                total_cost=Sum('total_cost'),
            )

            data = {
                'name': f"{project_type}",
                'data': list(
                    cost_list.values_list(
                        'total_cost', flat=True
                        )
                ),
                'color': self.proj_colour_dict.get(
                    project_type, self.project_colours[0]
                    )
                }

            category_data_source.append(data)
        category_chart_data = self.bar_chart_nostack_data.copy()
        category_chart_data['xAxis']['categories'] = self.string_months
        category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df(category_chart_data)

        return json_chart_data, chart_df


    def months_default_totals(self, form):
        """Default graph when 'All' months selected"""

        # Get all compute costs for the year

        category_data_source = []
        project_types = ["001", "002", "003", "004"]
        year = str(date.today().year)

        for project_type in project_types:
            cost_list = ComputeCosts.objects.filter(
                project__name__startswith=project_type,
                date__date__year=year
            ).order_by().values(
                'date__date__month'
            ).annotate(
                total_cost=Sum('total_cost'),
            )

            data = {
                'name': f"{project_type}",
                'data': list(
                    cost_list.values_list(
                        'total_cost', flat=True
                        )
                ),
                'color': self.proj_colour_dict.get(
                    project_type, self.project_colours[0]
                    )
                }

            category_data_source.append(data)
        category_chart_data = self.bar_chart_nostack_data.copy()
        category_chart_data['xAxis']['categories'] = self.string_months
        category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_nostack(category_chart_data)

        return json_chart_data, chart_df


    def default_daily_all_project(self, form):
        """
        Sets context when 'All' months selected with only project type(s)

        Parameters
        ----------
        proj_types :  list
            list of project types searched for e.g. ['001','002','003']
        year : str
            year that the date of the objects should belong to
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'compute_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # Filter by 'startswith' for each searched project type
        # For each proj add data to dict
        category_data_source = []
        count = -1
        year = str(date.today().year)
        # appended_list = []
        count += 1
        cost_list = ComputeCosts.objects.filter(
            date__date__year=year
        ).order_by().values(
            'date__date').annotate(total_cost=Sum('total_cost'))
        cost_dates = cost_list.annotate(date_unix=Func(F('date__date'),
                                        function='UNIX_TIMESTAMP',
                                        output_field=IntegerField())*1000)
        compute_data = {
            'name': "All projects",
            'data': list(
                cost_dates.values_list('date_unix',
                                       'total_cost')),  # flat=True when on var.
            'color': "rgb(46, 89, 2)"
        }

        category_data_source.append(compute_data)
        category_chart_data = self.time_chart_data.copy()
        category_chart_data['series'] = category_data_source

        # df = pd.DataFrame(list(cost_dates))
        # df['project'] = str(proj_type)
        # category_chart_data['xAxis']['categories'] = date_list
        # category_chart_data['xAxis']['series'] = dates
        # appended_list.append(df)
        # dfObj = pd.concat(appended_list, ignore_index=True)

        context = {
            'compute_data': json.dumps(category_chart_data),
            'form': form
        }

        return context


    def all_months_only_assay_types(self, assay_types, year, form):
        """
        Sets context when 'All' months selected, with only assay type(s)

        Parameters
        ----------
        assay_types :  list
            list of assay types searched for e.g. ['CEN','TWE','TSO500']
        year : str
            year that the date of the objects should belong to
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'compute_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        category_data_source = []
        # Filter by 'endswith' for each searched assay type
        count = -1
        for assay_type in assay_types:
            count += 1
            cost_list = ComputeCosts.objects.filter(
                project__name__endswith=assay_type,
                date__date__year=year
                ).order_by().values(
                    'date__date__month'
                    )

            compute_data = {
                'name': assay_type,
                'data': list(
                    cost_list.values_list(flat=True)
                ),
                'stack': 'Compute',  # live
                'color': self.assay_colour_dict.get(
                    assay_type, self.assay_colours[count]
                )
            }

            category_data_source.append(compute_data)

        category_chart_data = self.bar_chart_data.copy()
        category_chart_data['xAxis']['categories'] = self.string_months
        category_chart_data['series'] = category_data_source

        context = {
            'compute_data': json.dumps(category_chart_data),
            'form': form
        }

        return context


    def specific_month_proj_and_assay(
            self, project_type, assay_type, year,
            month, converted_month, form
    ):
        """
        Sets context when specific month is selected
        With one project type and one assay type

        Parameters
        ----------
        project_type: str
            string that the project name starts with
        assay_type :  str
            string that the project name ends with
        year : str
            year that the date of the objects should belong to e.g. '2022'
        month : str
            month that the date of the objects should belong to e.g. '5'
        converted_month : str
            the specified month as a string e.g. "May"
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'compute_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        category_data_source = []
        # Proj name starts wth project type and ends with assay type
        # Filter for specific year and month
        cost_list = ComputeCosts.objects.filter(
            project__name__startswith=project_type,
            project__name__endswith=assay_type,
            date__date__year=year,
            date__date__month=month
            ).aggregate(
                Cost=Sum('total_cost')
            )

        # Get the Cost aggregate for those projects
        # If QS empty, returns None which affects noData message
        # Keep as list with actual data or convert [None] to []
        Cost = cost_list.get('Cost')
        if Cost:
            Cost = [Cost]
        else:
            Cost = []

        Cost_data = {
            'name': f"{project_type}*{assay_type}",
            'data': Cost,
            'stack': 'Cost',
            'color': self.proj_colour_dict.get(
                project_type, self.project_colours[0]
            )
        }

        category_data_source.append(Cost_data)

        # As only one series, categories must be a list
        # Or Highcharts bug means it
        # Only shows the first letter of the category
        category_chart_data = self.bar_chart_data.copy()
        category_chart_data['xAxis']['categories'] = [converted_month]
        category_chart_data['series'] = category_data_source

        context = {
            'compute_data': json.dumps(category_chart_data),
            'form': form
        }

        return context

    def specific_month_only_proj_types(
        self, proj_types, year, month, converted_month, form
    ):
        """
        Sets context when specific month is selected
        With only project type(s) entered

        Parameters
        ----------
        proj_types: list
            list of project types searched for e.g. ['001','002','003']
        year : str
            year that the date of the objects should belong to e.g. '2022'
        month : str
            month that the date of the objects should belong to e.g. '5'
        converted_month : str
            the specified month as a string e.g. "May"
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'compute_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # Increase count per proj_type to assign new colours to bars
        category_data_source = []
        count = -1
        for proj_type in proj_types:
            count += 1
            cost_list = ComputeCosts.objects.filter(
                project__name__startswith=proj_type,
                date__date__year=year,
                date__date__month=month
            ).aggregate(
                Cost=Sum('total_cost')
                )

            Cost = cost_list.get('Cost')
            # If empty, returns None which wasn't showing noData message
            # Converted to empty list instead if [None]
            if Cost:
                Cost = [Cost]
            else:
                Cost = []

            Cost_data = {
                'name': proj_type,
                'data': Cost,
                'stack': 'Cost',
                'color': self.proj_colour_dict.get(
                    proj_type, self.project_colours[count]
                )
            }


            category_data_source.append(Cost_data)

        category_chart_data = self.bar_chart_data.copy()
        category_chart_data['xAxis']['categories'] = [converted_month]
        category_chart_data['series'] = category_data_source

        context = {
            'compute_data': json.dumps(category_chart_data),
            'form': form
        }

        return context

    def specific_month_only_assay_types(
        self, assay_types, year, month, converted_month, form
    ):
        """
        Sets context when specific month is selected
        With only assay type(s) entered

        Parameters
        ----------
        assay_types: list
            list of assay types searched for e.g. ['CEN','TWE','TSO500']
        year : str
            year that the date of the objects should belong to e.g. '2022'
        month : str
            month that the date of the objects should belong to e.g. '5'
        converted_month : str
            the specified month as a string e.g. "May"
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'compute_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        category_data_source = []
        count = -1
        for assay_type in assay_types:
            count += 1
            cost_list = ComputeCosts.objects.filter(
                project__name__endswith=assay_type,
                date__date__year=year,
                date__date__month=month
            ).aggregate(Cost=Sum('total_cost')
                )

            Cost = cost_list.get('Cost')
            if Cost:
                Cost = [Cost]
            else:
                Cost = []

            Cost_data = {
                'name': assay_type,
                'data': Cost,
                'stack': 'Cost',
                'color': self.assay_colour_dict.get(
                    assay_type, self.assay_colours[count]
                )
            }

            category_data_source.append(Cost_data)

        category_chart_data = self.bar_chart_data.copy()
        category_chart_data['xAxis']['categories'] = [converted_month]
        category_chart_data['series'] = category_data_source

        context = {
            'compute_data': json.dumps(category_chart_data),
            'form': form
        }

        return context

    def specific_month_no_proj_or_assay(
        self, year, month, converted_month, form
    ):
        """
        Sets context when specific month is selected
        With no project or assay types entered

        Parameters
        ----------
        year : str
            year that the date of the objects should belong to e.g. '2022'
        month : str
            month that the date of the objects should belong to e.g. '5'
        converted_month : str
            the specified month as a string e.g. "May"
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'compute_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        cost_list = ComputeCosts.objects.filter(
            date__date__year=year,
            date__date__month=month
        ).aggregate(Cost=Sum('total_cost')
            )

        category_data_source = [
            {
                "name": "All projects",
                "data": [cost_list.get('Cost')],
                'stack': 'Cost',
                'color': 'rgb(217,95,2)'
            }
        ]

        category_chart_data = self.bar_chart_data.copy()
        category_chart_data['xAxis']['categories'] = [converted_month]
        category_chart_data['series'] = category_data_source

        context = {
            'compute_data': json.dumps(category_chart_data),
            'form': form
        }

        return context

    def monthly_totals_byprojects(self, form):
        """
        Sets context to all projects all months when the form is not valid
        i.e. >1 project type and >1 assay type are entered

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'compute_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        Compute_totals = ComputeCosts.objects.filter(
            date__date__year=self.current_year
            ).order_by().values(
                'date__date__month'
                ).annotate(Cost=Sum('total_cost')
                    )

        category_data_source = [
            {
                "name": "All projects",
                "data": list(Compute_totals.values_list(
                    'Cost', flat=True
                    )
                    ),
                # 'stack': 'Cost',
                'color': 'rgb(217,95,2)'
            }
        ]

        category_chart_data = self.bar_chart_data.copy()
        category_chart_data['xAxis']['categories'] = self.string_months
        category_chart_data['series'] = category_data_source

        context = {
            'compute_data': json.dumps(category_chart_data),
            'form': form
        }

        return context


    def All_projects_by_months(self, form):
        """
        Sets context to all projects all months when the form is not valid
        i.e. >1 project type and >1 assay type are entered

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'compute_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        Compute_totals = ComputeCosts.objects.filter(
            date__date__year=self.current_year
            ).order_by().values(
                'date__date__month'
                ).annotate(Cost=Sum('total_cost')
                    )

        category_data_source = [
            {
                "name": "All projects",
                "data": list(Compute_totals.values_list(
                    'Cost', flat=True
                    )
                    ),
                'color': 'rgb(217,95,2)'
            }
        ]

        category_chart_data = self.bar_chart_data.copy()
        category_chart_data['xAxis']['categories'] = self.string_months
        category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_nostack(category_chart_data)

        return json_chart_data, chart_df


# Data tables

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
            the dataframe with Date, Type, State and Total Size
        """
        series_data = category_chart_data['series'].copy()
        dates = category_chart_data['xAxis']['categories'].copy()

        # As data column value contains a list, expand this over multiple rows
        # Explode fills in the relevant data for those extra rows
        exploded = pd.json_normalize(data = series_data).explode('data')

        # If data exists, expand the months table according to the df length
        # So the correct month can be added to the right row
        if dates:
            dates = dates * (int(len(exploded) / len(dates)))
            exploded['Date'] = dates
        # If no months exist (no data), keep months as empty list
        else:
            dates = []

        # Re-order columns
        exploded = exploded.reindex(
            columns=[
                'Date', 'name', 'stack', 'data'
            ]
        )
        exploded.rename(
            columns={
                "name": "Project Type",
                "stack": "Assay Type",
                'data': 'Total Cost ($)'
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


    def convert_to_df_projectonly(self, category_chart_data):
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
            the dataframe with Date, Type, State and Total Size
        """
        series_data = category_chart_data['series'].copy()
        dates = category_chart_data['xAxis']['categories'].copy()

        # As data column value contains a list, expand this over multiple rows
        # Explode fills in the relevant data for those extra rows
        exploded = pd.json_normalize(data = series_data).explode('data')

        # If data exists, expand the months table according to the df length
        # So the correct month can be added to the right row
        if dates:
            dates = dates * (int(len(exploded) / len(dates)))
            exploded['Date'] = dates
        # If no months exist (no data), keep months as empty list
        else:
            dates = []

        # Re-order columns
        exploded = exploded.reindex(
            columns=[
                'Date', 'name', 'data'
            ]
        )
        exploded.rename(
            columns={
                "name": "Project Type",
                'data': 'Total Cost ($)'
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


    def convert_to_df_monthly_by_proj_assay(self, category_chart_data):
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
            the dataframe with Date, Type, State and Total Size
        """
        series_data = category_chart_data['series'].copy()
        dates = category_chart_data['xAxis']['categories'].copy()

        # As data column value contains a list, expand this over multiple rows
        # Explode fills in the relevant data for those extra rows
        exploded = pd.json_normalize(data = series_data).explode('data')

        # If data exists, expand the months table according to the df length
        # So the correct month can be added to the right row
        if dates:
            dates = dates * (int(len(exploded) / len(dates)))
            exploded['Date'] = dates
        # If no months exist (no data), keep months as empty list
        else:
            dates = []

        # Re-order columns
        exploded = exploded.reindex(
            columns=[
                'Date', 'name', 'stack', 'data'
            ]
        )
        exploded.rename(
            columns={
                "name": "Project Type",
                "stack": "Assay Type",
                'data': 'Total Cost ($)'
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


    def convert_to_df_nostack(self, category_chart_data):
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
            the dataframe with Date, Type, State and Total Size
        """
        series_data = category_chart_data['series'].copy()
        dates = category_chart_data['xAxis']['categories'].copy()

        # As data column value contains a list, expand this over multiple rows
        # Explode fills in the relevant data for those extra rows
        exploded = pd.json_normalize(data = series_data).explode('data')

        # If data exists, expand the months table according to the df length
        # So the correct month can be added to the right row
        if dates:
            dates = dates * (int(len(exploded) / len(dates)))
            exploded['Date'] = dates
        # If no months exist (no data), keep months as empty list
        else:
            dates = []

        # Re-order columns
        exploded = exploded.reindex(
            columns=[
                'Date', 'name', 'data'
            ]
        )
        exploded.rename(
            columns={
                'Date': "Month",
                'name': "Project Type",
                'data': "Total Cost ($)"
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


    def convert_to_df_assayonly(self, category_chart_data):
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
            the dataframe with Date, Type, State and Total Size
        """
        series_data = category_chart_data['series'].copy()
        dates = category_chart_data['xAxis']['categories'].copy()

        # As data column value contains a list, expand this over multiple rows
        # Explode fills in the relevant data for those extra rows
        exploded = pd.json_normalize(data = series_data).explode('data')

        # If data exists, expand the months table according to the df length
        # So the correct month can be added to the right row
        if dates:
            dates = dates * (int(len(exploded) / len(dates)))
            exploded['Date'] = dates
        # If no months exist (no data), keep months as empty list
        else:
            dates = []

        # Re-order columns
        exploded = exploded.reindex(
            columns=[
                'Date', 'name', 'data'
            ]
        )
        exploded.rename(
            columns={
                "name": "Assay Type",
                'data': 'Total Cost ($)'
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


    def convert_to_df_timeseries(self, project_types):
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
            the dataframe with Date, Type, State and Total Size
        """

        df3 = pd.DataFrame()

        for project in project_types:
            cost_list = ComputeCosts.objects.all().filter(
                project__name__startswith=project).values('dx_id',
                                                          'date__date',
                                                          'project__name',
                                                          'total_cost',
                                                          'state',
                                                          'launched_by__user_name',
                                                          'executable_name__executable_name',
                                                          'runtime', )
            df3 = pd.DataFrame(cost_list)
            df3 = df3.assign(Project_type=project)
            df3.rename(
                columns={
                    'dx_id': 'DNAnexus ID',
                    'date__date': 'Date',
                    'project__name': 'Project',
                    'total_cost': 'Total Cost ($)',
                    'state': 'State',
                    'launched_by__user_name': 'Launched By',
                    'executable_name__executable_name': 'Executable',
                    'runtime': 'Runtime'
                },
                inplace = True
            )
            df3.append(df3)

        # Convert to HTML to easily show with DataTables

        chart_data = df3.to_html(
            index=False,
            classes='table table-striped"',
            justify='left'
        )

        return chart_data



    def convert_to_df_alldata_byproject_assay(self, project_types, assay_types):
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
            the dataframe with Date, Type, State and Total Size
        """

        dfObj = pd.DataFrame()

        for project in project_types:
            for assay in assay_types:
                cost_list = ComputeCosts.objects.all().filter(
                    project__name__startswith=project,
                    project__name__endswith=assay).values('dx_id',
                                                          'date__date',
                                                          'project__name',
                                                          'total_cost',
                                                          'state',
                                                          'launched_by__user_name',
                                                          'executable_name__executable_name',
                                                          'runtime', )
                df3 = pd.DataFrame(cost_list)
                df3 = df3.assign(Project_type=project)
                df3 = df3.assign(Assay_type=project)
                df3.rename(
                    columns={
                        'dx_id': 'DNAnexus ID',
                        'date__date': 'Date',
                        'project__name': 'Project',
                        'Assay_type': 'Assay Type',
                        'total_cost': 'Total Cost ($)',
                        'state': 'State',
                        'launched_by__user_name': 'Launched By',
                        'executable_name__executable_name': 'Executable',
                        'runtime': 'Runtime'
                    },
                    inplace = True
                )
                dfObj = dfObj.append(df3)

        # Convert to HTML to easily show with DataTables

        chart_data = dfObj.to_html(
            index=False,
            classes='table table-striped"',
            justify='left'
        )
        return chart_data


    def convert_to_df_alldata_by_assay(self, assay_types):
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
            the dataframe with Date, Type, State and Total Size
        """

        dfObj = pd.DataFrame()
        for assay in assay_types:
            cost_list = ComputeCosts.objects.all().filter(
                project__name__endswith=assay).values('dx_id',
                                                      'date__date',
                                                      'project__name',
                                                      'total_cost',
                                                      'state',
                                                      'launched_by__user_name',
                                                      'executable_name__executable_name',
                                                      'runtime', )
            df3 = pd.DataFrame(cost_list)
            df3 = df3.assign(Assay_type=assay)
            df3.rename(
                columns={
                    'dx_id': 'DNAnexus ID',
                    'date__date': 'Date',
                    'project__name': 'Project',
                    'Assay_type': 'Assay Type',
                    'total_cost': 'Total Cost ($)',
                    'state': 'State',
                    'launched_by__user_name': 'Launched By',
                    'executable_name__executable_name': 'Executable',
                    'runtime': 'Runtime'
                },
                inplace = True
            )
            dfObj = dfObj.append(df3)
        # Convert to HTML to easily show with DataTables

        chart_data = dfObj.to_html(
            index=False,
            classes='table table-striped"',
            justify='left'
        )
        return chart_data

