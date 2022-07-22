"""
This script holds plotting functions for visualising
jobs and analyses (executions) used in views.py
"""

import json
import plotly.express as px
import plotly.graph_objects as pgo
import calendar
from datetime import date

from dashboard.models import ComputeCosts, Dates, Executables, Projects, StorageCosts
from django.conf import settings
from django.db.models import Func, F, Sum, IntegerField
from scripts import DNAnexus_queries as dx_queries
from scripts import date_conversion as dc
import pandas as pd

class UserPlotFunctions():
    """
    Class of plotting functions for executions graph.
    """

    def __init__(self) -> None:
        self.current_year = dx_queries.no_of_days_in_month()[0].split('-')[0]
        # Get Plotly discrete colour lists
        self.project_colours = px.colors.qualitative.Set1
        self.assay_colours = px.colors.qualitative.Bold
        self.user_colours = px.colors.qualitative.Bold
        # Specify colours for specific types of projects or assays
        # So don't change on diff numbers of types/assays during filtering
        self.proj_colour_dict = settings.PROJ_COLOUR_DICT
        self.assay_colour_dict = settings.ASSAY_COLOUR_DICT
        self.user_colour_dict = settings.USER_COLOUR_DICT
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
        self.month_lookup = list(calendar.month_name)
        self.better_string_months = sorted(self.string_months, key=self.month_lookup.index)

        # self.string_months.reverse()

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
                    'text': 'Compute cost ($)'
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
            'series': [],
            "tooltip": {
                "pointFormat": "{series.name}: <b>${point.y:.2f}"
                "</b><br>{series.options.stack}<br>"
            }
        }
        self.time_chart_data2 = {
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
            'yAxis': [{
                       'title': {
                         'text': 'Compute cost ($)'
                       },
                       'height': '50%',
                       'lineWidth': 2
                     },
                      {
                       'title': {
                         'text': 'Temperature'
                       },
                       'top': '50%',
                       'height': '50%',
                       'offset': 0,
                       'lineWidth': 2
                        },
                        {
                         'title': {
                           'text': 'Temperature2'
                         },
                         'bottom': '30%',
                         'height': '50%',
                         'offset': 0,
                         'lineWidth': 2
                          }],
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
            'series': [],
            "tooltip": {
                "pointFormat": "{series.name}: <b>${point.y:.2f}"
                "</b><br>{series.options.stack}<br>"
            }
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
                    'text': 'Compute cost ($)'
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
            "tooltip": {
                "pointFormat": "{series.name}: <b>${point.y:.2f}"
                "</b><br>{series.options.stack}<br>"
            }
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
                    'text': 'Compute cost ($)'
                },
            },
            'setOptions': {
                'lang': {
                    'thousandsSep': ',',
                    'noData': 'No data to display'
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
            )
        ) for entry in cost_list
        ]

        converted_months = [(
            calendar.month_name[int(month_tuple[0])], month_tuple[1]
        ) for month_tuple in months
        ]

        string_months = list(map(" ".join, converted_months))

        return string_months


    def get_users_as_str(self, Queryset):
        """
        Converts a list of month years to stringified month-years
        Parameters
        ----------
        Queryset : Django query set as a list of dicts
        e.g. test =
        [{
            'launched_by__user_name': 'user-1',
        },
        {
            'launched_by__user_name': 'user-2',
        }]
        Returns
        -------
        string_months : list
            list of months in more readable form for plots
        e.g.
        get_users_as_str(test)
            >> ['user-1', 'user-2']
        """
        users = [(str(
            entry.get('launched_by__user_name'))
        ) for entry in Queryset
        ]
        users_list = []
        for user in users:
            users_list.append(user.split("-")[1])

        return users_list


    # def all_months_default(self, form):
    #     """
    #     Default graph when 'All' months selected
    #     """

    #     # Get all compute costs for the year

    #     category_data_source = []
    #     User_totals = ComputeCosts.objects.filter(
    #             project__name__endswith=assay_type,
    #             date__date__range=[month_start, month_end]
    #         ).values('launched_by__user_name'
    #                  ).annotate(Cost=Sum('total_cost'))
    #     string_users = self.get_users_as_str(User_totals)

    #     data = {
    #             'name': f"General Trends {year}",
    #             'data': list(
    #                 User_totals.values_list(
    #                     'total_cost', flat=True
    #                     )
    #             ),
    #             'stack': 'total_cost',
    #         }

    #     category_data_source.append(data)
    #     category_chart_data = self.bar_chart_data.copy()
    #     category_chart_data['xAxis']['categories'] = self.better_string_months
    #     category_chart_data['series'] = category_data_source

    #     json_chart_data = json.dumps(category_chart_data)

    #     chart_df = self.convert_to_df(category_chart_data)

    #     return json_chart_data, chart_df



    def daily_month_range_all_byproject(self, month_start, month_end,
                                              project_types, form):
        """
        Filters data when months are selected and projects are specified,
        and returns data by monthly format.

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'leaderboard_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # Filter by 'startswith' for each searched project type
        # For each proj add data to dict
        category_data_source = []
        count = -1
        count_axis = 0
        project_types = self.str_to_list(project_types)
        user_chart = {
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
                    'yAxis': [{
                        'allowDecimals': 'false',
                        'min': '0',
                        'title': {
                            'text': 'Compute cost ($)'
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
                    {
                        'allowDecimals': 'false',
                        'min': '0',
                        'title': {
                            'text': 'Compute cost 2 ($)'
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
                    }],
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
                    'series': [],
                    "tooltip": {
                        "pointFormat": "{series.name}: <b>${point.y:.2f}"
                        "</b><br>{series.options.stack}<br>"
                    }
                    }
        userTotals_initial = ComputeCosts.objects.filter(
                    project__name__startswith=project_types[0],
                    date__date__range=[month_start, month_end]
                ).values('launched_by__user_name',
                         'date__date__month',
                         'date__date__year'
                         ).annotate(Cost=Sum('total_cost'))
        users = set(self.get_users_as_str(userTotals_initial))
        category_chart_data = user_chart
        for project_type in project_types:
            count_axis += 1
            for user in users:
                count += 1
                usertotals = ComputeCosts.objects.filter(
                    project__name__startswith=project_type,
                    date__date__range=[month_start, month_end],
                    launched_by__user_name__endswith=user
                ).values('launched_by__user_name',
                         'date__date__day',
                         'date__date__month',
                         'date__date__year'
                         ).annotate(Cost=Sum('total_cost'))
                userTotalsDates = usertotals.annotate(date_unix=Func(F('date__date'),
                                                function='UNIX_TIMESTAMP',
                                                output_field=IntegerField())*1000)

                leaderboard_data = {
                    'name': f"{user}",
                    'type': 'column',
                    'data': list(
                        userTotalsDates.values_list('date_unix',
                                                    'Cost')),
                    # 'color': self.proj_colour_dict.get(
                    #     project_type, self.project_colours[0]
                    #     ),
                    'yAxis': count_axis,
                    }
                category_data_source.append(leaderboard_data)
            category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_alldata_by_project(month_start,
                                                         month_end,
                                                         project_types)

        return json_chart_data, chart_df



    def daily_month_range_byproject(self, month_start, month_end,
             project_types, form):
        """
        Filters data when no months selected but projects are specified,
        and returns data by monthly format.

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'leaderboard_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # Filter by 'startswith' for each searched project type
        # For each proj add data to dict
        category_data_source = []
        count = -1
        project_types = self.str_to_list(project_types)
        list_of_axis = []
        percentage = 100 / len(project_types)
        for index, project in enumerate(project_types):
            if len(project_types) == 1:
                percentage = 100
                plot_height = 600
                y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'height': f'{percentage}%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                list_of_axis.append(y_axis_dict)
            elif len(project_types) == 2:
                percentage = 50
                plot_height = 800
                if index == 0:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'0%',
                               'height': f'{percentage}%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
                elif index == 1:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'{percentage}%',
                               'height': f'{percentage}%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
            elif len(project_types) == 3:
                percentage = 33.33
                plot_height = 800
                if index == 0:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'0%',
                               'height': f'30%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
                elif index == 1:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'{percentage}%',
                               'height': f'30%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
                elif index == 2:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'{percentage*2}%',
                               'height': f'30%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
            elif len(project_types) == 4:
                percentage = 25
                plot_height = 800
                if index == 0:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'0%',
                               'height': f'20%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
                elif index == 1:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'{percentage}%',
                               'height': f'20%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
                elif index == 2:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'{percentage*2}%',
                               'height': f'20%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
                elif index == 3:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'{percentage*3}%',
                               'height': f'20%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
        multi_axis_time_chart = {
            'chart': {
                'zoomType': 'x',
                'type': 'column',
                'width': 1200,
                'height':plot_height,
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
            'yAxis': list_of_axis,
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
            'series': [],
            "tooltip": {
                "pointFormat": "{series.name}: <b>${point.y:.2f}"
                "</b><br>{series.options.stack}<br>"
            }
        }
        users_list = []
        for project in project_types:
            userTotals_initial = ComputeCosts.objects.filter(
                    date__date__range=[month_start, month_end]
                ).values('launched_by__user_name',
                         'date__date__month',
                         'date__date__year'
                         ).annotate(Cost=Sum('total_cost'))
            users = set(self.get_users_as_str(userTotals_initial))
            for user in users:
                users_list.append(user)
        users_set = set(users_list)
        count_axis = -1
        for project in project_types:
            count_axis +=1
            for user in users_set:
                count += 1
                cost_list = ComputeCosts.objects.filter(
                    project__name__startswith=project,
                    date__date__range=[month_start, month_end],
                    launched_by__user_name__endswith=user
                ).order_by().values(
                    'date__date__month',
                    'date__date__year'
                    ).annotate(total_cost=Sum('total_cost'))

                cost_dates = cost_list.annotate(date_unix=Func(F('date__date'),
                                                function='UNIX_TIMESTAMP',
                                                output_field=IntegerField())*1000)
                if cost_dates:
                    leaderboard_data = {
                        'name': f"{project}-{user}",
                        'data': list(
                            cost_dates.values_list('date_unix',
                                                   'total_cost')),  # flat=True when on var.
                        'color': self.user_colour_dict.get(
                            user, self.user_colours[0]
                            ),
                        'yAxis': count_axis
                        }

                    category_data_source.append(leaderboard_data)
                    category_chart_data = multi_axis_time_chart  # self.time_chart_data2.copy()
                    category_chart_data['series'] = category_data_source
        json_chart_data = json.dumps(category_chart_data)
        chart_df = self.convert_to_df_alldata_by_project

        return json_chart_data, chart_df


    def daily_month_range_allproject_home(self, month_start, month_end,
                                          form):
        """
        Sets context when no months selected with no projects specified.

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'leaderboard_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # Filter by 'startswith' for each searched project type
        # For each proj add data to dict
        category_data_source = []
        count = -1
        users_list = []
        userTotals_initial = ComputeCosts.objects.filter(
                    date__date__range=[month_start, month_end]
                ).values('launched_by__user_name',
                         'date__date__month',
                         'date__date__year'
                         ).annotate(Cost=Sum('total_cost'))
        users = set(self.get_users_as_str(userTotals_initial))
        for user in users:
            users_list.append(user)
        users_set = set(users_list)
        for user in users_set:
            count += 1
            cost_list = ComputeCosts.objects.filter(
                date__date__range=[month_start, month_end],
                launched_by__user_name__endswith=user
            ).order_by().values(
                'date__date__month',
                'date__date__year'
                ).annotate(total_cost=Sum('total_cost'))
            cost_dates = cost_list.annotate(date_unix=Func(F('date__date'),
                                            function='UNIX_TIMESTAMP',
                                            output_field=IntegerField())*1000)
            if cost_dates:
                leaderboard_data = {
                    'name': f"{user}",
                    'data': list(
                        cost_dates.values_list('date_unix',
                                               'total_cost')),  # flat=True when on var.
#                    'color': self.user_colour_dict.get(
#                        user, self.user_colours[0]
#                        )
                    }
                category_data_source.append(leaderboard_data)
                category_chart_data = self.time_chart_data.copy()
                category_chart_data['series'] = category_data_source
        json_chart_data = json.dumps(category_chart_data)

        return json_chart_data


    def daily_month_range_byuser(self, month_start, month_end,
             user_types, form):
        """
        Sets context when no months selected with no projects specified.

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'leaderboard_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # Filter by 'startswith' for each searched project type
        # For each proj add data to dict
        category_data_source = []
        count = -1
        user_types = self.str_to_list(user_types)
        multi_axis_time_chart = {
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
                    'text': 'Compute cost ($)'
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
            'series': [],
            "tooltip": {
                "pointFormat": "{series.name}: <b>${point.y:.2f}"
                "</b><br>{series.options.stack}<br>"
            }
        }
        for user in user_types:
            count += 1
            cost_list = ComputeCosts.objects.filter(
                date__date__range=[month_start, month_end],
                launched_by__user_name__endswith=user
            ).order_by().values(
                'date__date__month',
                'date__date__year'
                ).annotate(total_cost=Sum('total_cost'))

            cost_dates = cost_list.annotate(date_unix=Func(F('date__date'),
                                            function='UNIX_TIMESTAMP',
                                            output_field=IntegerField())*1000)
            if cost_dates:
                leaderboard_data = {
                    'name': f"{user}",
                    'data': list(
                        cost_dates.values_list('date_unix',
                                               'total_cost')),
                    'color': self.user_colour_dict.get(
                        user, self.user_colours[0]
                        )
                    }
                category_data_source.append(leaderboard_data)
                category_chart_data = multi_axis_time_chart  # self.time_chart_data2.copy()
                category_chart_data['series'] = category_data_source
        json_chart_data = json.dumps(category_chart_data)
        chart_df =  self.convert_to_df_alldata_by_user(month_start, month_end,
                                                  user_types)
        return json_chart_data, chart_df


    def daily_month_range_byusers_projects(self, month_start, month_end,
             project_types, user_types, form):
        """
        Sets context when no months selected with no projects specified.

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'leaderboard_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # Filter by 'startswith' for each searched project type
        # For each proj add data to dict
        category_data_source = []
        count = -1
        project_types = self.str_to_list(project_types)
        user_types = self.str_to_list(user_types)
        # user_list = []
        # for user in user_types:
        #     user_suffix = user.split("-")[1]
        #     user_list.append(user_suffix)
        list_of_axis = []
        for index, project in enumerate(project_types):
            if len(project_types) == 1:
                percentage = 100
                y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'height': f'{percentage}%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                list_of_axis.append(y_axis_dict)
            elif len(project_types) == 2:
                percentage = 50
                height = 45
                if index == 0:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'0%',
                               'height': f'{height}%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
                elif index == 1:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'{percentage}%',
                               'height': f'{height}%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
            elif len(project_types) == 3:
                percentage = 33.33
                if index == 0:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'0%',
                               'height': f'30%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
                elif index == 1:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'{percentage}%',
                               'height': f'30%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
                elif index == 2:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'{percentage*2}%',
                               'height': f'30%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
            elif len(project_types) == 4:
                percentage = 25
                if index == 0:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'0%',
                               'height': f'22%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
                elif index == 1:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'{percentage}%',
                               'height': f'22%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
                elif index == 2:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'{percentage*2}%',
                               'height': f'22%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
                elif index == 3:
                    y_axis_dict = {'title': {
                                 'text': f'{project} Compute Costs ($)'
                               },
                               'top': f'{percentage*3}%',
                               'height': f'22%',
                               'offset': 0,
                               'lineWidth': 2
                             }
                    list_of_axis.append(y_axis_dict)
        multi_axis_time_chart = {
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
            'yAxis': list_of_axis,
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
            'series': [],
            "tooltip": {
                "pointFormat": "{series.name}: <b>${point.y:.2f}"
                "</b><br>{series.options.stack}<br>"
            }
        }

        count_axis = -1
        for project in project_types:
            count_axis +=1
            for user in user_types:
                count += 1
                cost_list = ComputeCosts.objects.filter(
                    project__name__startswith=project,
                    date__date__range=[month_start, month_end],
                    launched_by__user_name__endswith=user
                ).order_by().values(
                    'date__date__month',
                    'date__date__year'
                    ).annotate(total_cost=Sum('total_cost'))

                cost_dates = cost_list.annotate(date_unix=Func(F('date__date'),
                                                function='UNIX_TIMESTAMP',
                                                output_field=IntegerField())*1000)
                if cost_dates:
                    leaderboard_data = {
                        'name': f"{project}-{user}",
                        'data': list(
                            cost_dates.values_list('date_unix',
                                                   'total_cost')),  # flat=True when on var.
                        'color': self.user_colour_dict.get(
                            user, self.user_colours[0]
                            ),
                        'yAxis': count_axis
                        }

                    category_data_source.append(leaderboard_data)
                    category_chart_data = multi_axis_time_chart  # self.time_chart_data2.copy()
                    category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)
        chart_df = self.convert_to_df_alldata_byproject_user(
            month_start, month_end, project_types, user_types)
        return json_chart_data, chart_df


    def daily_month_range_all_byassay_types(self, month_start, month_end,
                                              assay_types, form):
        """
        Sets context when no months selected with no projects specified.

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'leaderboard_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # Filter by 'startswith' for each searched project type
        # For each proj add data to dict

        category_data_source = []
        count = -1

        assay_types = self.str_to_list(assay_types)
        for assay_type in assay_types:
            count += 1
            User_totals = ComputeCosts.objects.filter(
                project__name__endswith=assay_type,
                date__date__range=[month_start, month_end]
            ).values('launched_by__user_name'
                     ).annotate(Cost=Sum('total_cost'))

            User_totals_dates = User_totals.annotate(date_unix=Func(F('date__date'),
                                            function='UNIX_TIMESTAMP',
                                            output_field=IntegerField())*1000)
            leaderboard_data = {
                'name': assay_type,
                'data': list(
                    User_totals_dates.values_list('date_unix',
                                           'total_cost')),  # flat=True when on var.
                # 'color': self.assay_colour_dict.get(
                #     assay_type, self.assay_colours[0]
                #     )
            }

            category_data_source.append(leaderboard_data)
            category_chart_data = self.time_chart_data.copy()
            category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_alldata_by_assay(month_start,
                                                       month_end,
                                                       assay_types)

        return json_chart_data, chart_df


    def daily_month_range_all_byproject_and_assay(self,
                                                    month_start, month_end,
                                                    project_types, assay_types,
                                                    form):
        """
        Sets context when no months selected with no projects specified.

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'leaderboard_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # Filter by 'startswith' for each searched project type
        # For each proj add data to dict

        category_data_source = []
        count = -1

        assay_types = self.str_to_list(assay_types)
        project_types = self.str_to_list(project_types)
        for proj_type in project_types:
            for assay_type in assay_types:
                count += 1
                cost_list = ComputeCosts.objects.filter(
                    project__name__startswith=proj_type,
                    project__name__endswith=assay_type,
                    date__date__range=[month_start, month_end]
                ).order_by().values(
                    'date__date__month',
                    'date__date__year'
                    ).annotate(total_cost=Sum('total_cost'))

                cost_dates = cost_list.annotate(date_unix=Func(F('date__date'),
                                                function='UNIX_TIMESTAMP',
                                                output_field=IntegerField())*1000)

                leaderboard_data = {
                    'name': f"{proj_type}-{assay_type}",
                    'data': list(
                        cost_dates.values_list('date_unix',
                                               'total_cost')),  # flat=True when on var.
                    # 'color': self.assay_colour_dict.get(
                    #     assay_type, self.assay_colours[0]
                    #     )
                }

                category_data_source.append(leaderboard_data)
                category_chart_data = self.time_chart_data.copy()
                category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_alldata_byproject_assay(month_start,
                                                              month_end,
                                                              project_types,
                                                              assay_types)

        return json_chart_data, chart_df


    def default_month_range_daily_all_project(self, month_start,
                                              month_end, form):
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
            'leaderboard_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # Filter by 'startswith' for each searched project type
        # For each proj add data to dict
        category_data_source = []

        cost_list = ComputeCosts.objects.filter(
            date__date__range=[month_start, month_end]
        ).order_by().values(
            'date__date__month',
            'date__date__year'
            ).annotate(total_cost=Sum('total_cost'))

        cost_dates = cost_list.annotate(date_unix=Func(F('date__date'),
                                        function='UNIX_TIMESTAMP',
                                        output_field=IntegerField())*1000)

        leaderboard_data = {
            'name': "All projects",
            'data': list(
                cost_dates.values_list('date_unix',
                                       'total_cost')),  # flat=True when on var.
            'color': "rgb(46, 89, 2)"
        }

        category_data_source.append(leaderboard_data)
        category_chart_data = self.time_chart_data.copy()
        category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)
        chart_df = self.all_data_default_daily(month_start, month_end)

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
            'leaderboard_data': data to pass to Highcharts,
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
        ).values('launched_by__user_name'
            ).order_by().values(
            'date__date__month'
            ).annotate(total_cost=Sum('total_cost'))
        cost_dates = cost_list.annotate(date_unix=Func(F('date__date'),
                                        function='UNIX_TIMESTAMP',
                                        output_field=IntegerField())*1000)
        leaderboard_data = {
            'name': "All projects",
            'data': list(
                cost_dates.values_list('date_unix',
                                       'total_cost')),
            'color': "rgb(46, 89, 2)"
        }

        category_data_source.append(leaderboard_data)
        category_chart_data = self.time_chart_data.copy()
        category_chart_data['series'] = category_data_source

        # df = pd.DataFrame(list(cost_dates))
        # df['project'] = str(proj_type)
        # category_chart_data['xAxis']['categories'] = date_list
        # category_chart_data['xAxis']['series'] = dates
        # appended_list.append(df)
        # dfObj = pd.concat(appended_list, ignore_index=True)

        context = {
            'leaderboard_data': json.dumps(category_chart_data),
            'form': form
        }

        return context


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
            'leaderboard_data': data to pass to Highcharts,
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
            leaderboard_data = {
                'name': proj_type,
                'data': list(
                    cost_dates.values_list('date_unix',
                                           'total_cost')),  # flat=True when on var.
                'color': self.proj_colour_dict.get(
                    proj_type, self.project_colours[0]
                    )
            }

            category_data_source.append(leaderboard_data)
            category_chart_data = self.time_chart_data.copy()
            category_chart_data['series'] = category_data_source

        context = {
            'leaderboard_data': json.dumps(category_chart_data),
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
            'leaderboard_data': data to pass to Highcharts,
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
        leaderboard_data = {
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

        category_data_source.append(leaderboard_data)

        category_chart_data = self.bar_chart_data.copy()
        category_chart_data['xAxis']['categories'] = self.better_string_months
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
        category_chart_data['xAxis']['categories'] = self.better_string_months
        category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_alldata_by_project()

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
        category_chart_data['xAxis']['categories'] = self.better_string_months
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
        #                        "categories": self.better_string_months})
        # # for month in self.better_string_months:
        #     categories.append({"name": f"{month}",
        #                        "categories": project_types})
        category_chart_data['xAxis']['categories'] = self.better_string_months
        category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_alldata_byproject_assay(project_types,
                                                              assay_types)

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
        category_chart_data['xAxis']['categories'] = self.better_string_months
        category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_nostack(category_chart_data)

        return json_chart_data, chart_df


    def all_months_only_assay_types(self, month_start,
                                    month_end, assay_types, form):
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
            'leaderboard_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        category_data_source = []
        # Filter by 'endswith' for each searched assay type
        count = -1
        for assay_type in assay_types:
            count += 1
            User_totals = ComputeCosts.objects.filter(
                project__name__endswith=assay_type,
                date__date__range=[month_start, month_end]
            ).values('launched_by__user_name'
                     ).annotate(Cost=Sum('total_cost'))
            string_users = self.get_users_as_str(User_totals)

            leaderboard_data = {
                'name': assay_type,
                'data': list(
                    User_totals.values_list(flat=True)
                ),
                'stack': 'Compute',  # live
                'color': self.assay_colour_dict.get(
                    assay_type, self.assay_colours[count]
                )
            }

            category_data_source.append(leaderboard_data)

        category_chart_data = self.bar_chart_data.copy()
        category_chart_data['xAxis']['categories'] = string_users
        category_chart_data['series'] = category_data_source

        context = {
            'leaderboard_data': json.dumps(category_chart_data),
            'form': form
        }

        return context


    def All_projects_by_months(self, month_start,
                               month_end, form):
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
            'leaderboard_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """

        User_totals = ComputeCosts.objects.filter(
            date__date__range=[month_start, month_end]
            ).order_by().values('launched_by__user_name'
                     ).annotate(Cost=Sum('total_cost'))
        string_users = self.get_users_as_str(User_totals)

        category_data_source = [
            {
                "name": "All projects",
                "data": list(User_totals.values_list(
                    'Cost', flat=True
                    )
                    ),
                'color': 'rgb(217,95,2)'
            }
        ]

        category_chart_data = self.bar_chart_data.copy()
        category_chart_data['xAxis']['categories'] = string_users
        category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_alldata_default(month_start, month_end)

        return json_chart_data, chart_df


    def All_projects_by_users(self, month_start,
                               month_end, form):
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
            'leaderboard_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """

        User_totals = ComputeCosts.objects.filter(
            date__date__range=[month_start, month_end]
            ).order_by().values('launched_by__user_name'
                     ).annotate(Cost=Sum('total_cost'))
        string_users = self.get_users_as_str(User_totals)

        category_data_source = [
            {
                "name": "All projects",
                "data": list(User_totals.values_list(
                    'Cost', flat=True
                    )
                    ),
                'color': 'rgb(217,95,2)'
            }
        ]

        category_chart_data = self.bar_chart_data.copy()
        category_chart_data['xAxis']['categories'] = string_users
        category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_alldata_default(month_start, month_end)

        return json_chart_data, chart_df


    def all_data_default_monthly(self, month_start, month_end):
        """
        Collects all data and annotates by month and user.

        Args:
            month_start (date): start of data range
            month_end (date): end of data range

        Returns:
            df: df of all data by user and month
        """
        #dfObj = pd.DataFrame()
        all_data_by_user = ComputeCosts.objects.filter(
            date__date__range=[month_start, month_end]
            ).order_by().values('launched_by__user_name',
                                'date__date__month'
                     ).annotate(Cost=Sum('total_cost'))
        all_data_by_user_df = pd.DataFrame(all_data_by_user)
        all_data_by_user_df['launched_by__user_name'] = all_data_by_user_df['launched_by__user_name'].apply(
            lambda x: x.split('-')[1])
        all_data_by_user_df['Cost'] = all_data_by_user_df['Cost'].apply(
            lambda x: round(x, 2))
        # all_data_by_user_df.rename(
        #     columns={
        #         'dx_id': 'DNAnexus ID',
        #         'date__date': 'Date',
        #         'project__name': 'Project',
        #         'Assay_type': 'Assay Type',
        #         'total_cost': 'Total Cost ($)',
        #         'launched_by__user_name': 'User',
        #         'executable_name__executable_name': 'Executable',
        #         'runtime': 'Runtime*'
        #     },
        #     inplace = True
        # )
        #dfObj = dfObj.append(all_data_by_user_df)
        # Convert to HTML to easily show with DataTables

        chart_data = all_data_by_user_df.to_html(
            index=False,
            classes='table table-striped"',
            justify='left'
        )
        return chart_data


    def all_data_default_daily(self, month_start, month_end):
        """
        Collects all data and annotates by month and user.

        Args:
            month_start (date): start of data range
            month_end (date): end of data range

        Returns:
            df: df of all data by user and month
        """
        all_data_by_user = ComputeCosts.objects.filter(
            date__date__range=[month_start, month_end]
            ).order_by().values('launched_by__user_name',
                                'date__date'
                     ).annotate(Cost=Sum('total_cost'))
        all_data_by_user_df = pd.DataFrame(all_data_by_user)
        all_data_by_user_df['launched_by__user_name'] = all_data_by_user_df['launched_by__user_name'].apply(
            lambda x: x.split('-')[1])
        all_data_by_user_df['total_cost'] = all_data_by_user_df['total_cost'].apply(
            lambda x: round(x, 2))
        all_data_by_user_df.rename(
            columns={
                'dx_id': 'DNAnexus ID',
                'date__date': 'Date',
                'project__name': 'Project',
                'Assay_type': 'Assay Type',
                'total_cost': 'Total Cost ($)',
                'launched_by__user_name': 'User',
                'executable_name__executable_name': 'Executable',
                'runtime': 'Runtime*'
            },
            inplace = True
        )
        dfObj = dfObj.append(all_data_by_user_df)
        # Convert to HTML to easily show with DataTables

        chart_data = dfObj.to_html(
            index=False,
            classes='table table-striped"',
            justify='left'
        )
        return chart_data


    # def monthly_byproject(self, project_types, form):
    #     """Graph showing monthly total cost by projects (startswith filter)"""

    #     # Get all compute costs for the year
    #     project_types = self.str_to_list(project_types)
    #     category_data_source = []
    #     year = str(date.today().year)

    #     for project_type in project_types:
    #         cost_list = ComputeCosts.objects.filter(
    #             project__name__startswith=project_type,
    #             date__date__year=year
    #         ).order_by().values(
    #             'date__date__month'
    #         ).annotate(
    #             total_cost=Sum('total_cost'),
    #         )

    #         data = {
    #             'name': f"{project_type}",
    #             'data': list(
    #                 cost_list.values_list(
    #                     'total_cost', flat=True
    #                     )
    #             ),
    #             'color': self.proj_colour_dict.get(
    #                 project_type, self.project_colours[0]
    #                 )
    #             }

    #         category_data_source.append(data)
    #     category_chart_data = self.bar_chart_nostack_data.copy()
    #     category_chart_data['xAxis']['categories'] = self.better_string_months
    #     category_chart_data['series'] = category_data_source

    #     json_chart_data = json.dumps(category_chart_data)

    #     chart_df = self.convert_to_df_projectonly(category_chart_data)

    #     return json_chart_data, chart_df


    def Monthly_by_project(self, month_start, month_end, project_types, form):
        """
        TO BE FIXED
        Filters the data by project and displays by months.

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'leaderboard_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        User_totals = ComputeCosts.objects.filter(
            date__date__range=[month_start, month_end]
            ).values('launched_by__user_name',
                     'date__date__month'
                ).order_by('date__date__month').annotate(Cost=Sum('total_cost'))
        # string_users = set(self.get_users_as_str(User_totals))
        category_data_source = []
        # users_list = []
        project_types = self.str_to_list(project_types)
        for project in project_types:
            User_totals = ComputeCosts.objects.filter(
                project__name__startswith=project,
                date__date__range=[month_start, month_end]
                ).values('date__date__month',
                         'date__date__year',
                         'launched_by__user_name'
                         ).order_by('date__date__month'
                                    ).annotate(Cost=Sum('total_cost'))
            print(User_totals)
            # for user in users:
            #     users_list.append(user)
            # users_set = set(users_list)
            string_users = set(self.get_users_as_str(User_totals))
            # daily_month_range_byproject for reference
            for user in string_users:
                print(user)
                data ={
                        "name": f"{project}-{user}",
                        "data": list(User_totals.filter(
                            launched_by__user_name__endswith = user).values_list(
                                'Cost', flat=True
                            )),
                        # 'color': 'rgb(217,95,2)'
                    }
                category_data_source.append(data)
        category_chart_data = self.bar_chart_data.copy()
        category_chart_data['xAxis']['categories'] = self.better_string_months
        category_chart_data['series'] = category_data_source
        print(self.better_string_months)
        json_chart_data = json.dumps(category_chart_data)
        print(json_chart_data)
        chart_df = self.convert_to_df_alldata_by_project(month_start,
                                                         month_end,
                                                         project_types)

        return json_chart_data, chart_df


    def Monthly_by_project_and_users(self, month_start,
                                     month_end, project_types,
                                     user_types, form):
        """
        TO BE FIXED
        Filters the data by project and user and displays by months.

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'leaderboard_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # User_totals = ComputeCosts.objects.filter(
        #     date__date__range=[month_start, month_end]
        #     ).values('launched_by__user_name',
        #              'date__date__month'
        #         ).order_by('date__date__month').annotate(Cost=Sum('total_cost'))
        category_data_source = []
        project_types = self.str_to_list(project_types)
        user_types = self.str_to_list(user_types)
        number_of_yaxis = len(project_types)
        list_of_yaxes = []
        for index, project in enumerate(project_types):
            if number_of_yaxis < 2:
                plot_height = 600
                yaxis_dict = {
                'allowDecimals': 'false',
                'min': '0',
                'title': {
                    'text': f'Compute cost for {project} ($)'
                },
                'stackLabels': {
                    'enabled': 'true',
                    'allowOverlap': 'true',
                    'style': {
                        'fontWeight': 'bold',
                        'color': 'gray'
                    },
                    'format': "{stack}"
                }}
                list_of_yaxes.append(yaxis_dict)
            elif number_of_yaxis == 2:
                plot_height = 600
                if index == 1:
                    top = '50%'
                    offset = 20
                else:
                    top= '0%'
                    offset = 0
                yaxis_dict = {
                    'allowDecimals': 'false',
                    'min': '0',
                    'title': {
                        'text': f'Compute cost for {project} ($)'
                    },
                    'height': '50%',
                    'top': top,
                    'offset': offset,
                    'stackLabels': {
                        'enabled': 'true',
                        'allowOverlap': 'true',
                        'style': {
                            'fontWeight': 'bold',
                            'color': 'gray'
                        },
                        'format': "{stack}"
                    }}
                list_of_yaxes.append(yaxis_dict)
            elif number_of_yaxis == 3:
                plot_height = 800
                height = '30%'
                if index == 0:
                    top = '0%'
                    offset = 0
                if index == 1:
                    top = '33.33%'
                    offset = 0
                elif index == 2:
                    top = '66.66%'
                    offset = 0
                else:
                    print("Error")
                yaxis_dict = {
                    'allowDecimals': 'false',
                    'min': '0',
                    'title': {
                        'text': f'Compute cost for {project} ($)'
                    },
                    'height': height,
                    'top': top,
                    'offset': offset,
                    'stackLabels': {
                        'enabled': 'true',
                        'allowOverlap': 'true',
                        'style': {
                            'fontWeight': 'bold',
                            'color': 'gray'
                        },
                        'format': "{stack}"
                    }}
                list_of_yaxes.append(yaxis_dict)
            elif number_of_yaxis == 4:
                plot_height = 800
                height = '22%'
                percentage = 25
                offset = 0
                if index == 0:
                    top = '0%'
                if index == 1:
                    top = f'{percentage}%'
                elif index == 2:
                    top = f'{percentage*2}%'
                elif index == 3:
                    top = f'{percentage*3}%'
                else:
                    print("Error")
                yaxis_dict = {
                    'allowDecimals': 'false',
                    'min': '0',
                    'title': {
                        'text': f'Compute cost for {project} ($)'
                    },
                    'height': height,
                    'top': top,
                    'offset': offset,
                    'stackLabels': {
                        'enabled': 'true',
                        'allowOverlap': 'true',
                        'style': {
                            'fontWeight': 'bold',
                            'color': 'gray'
                        },
                        'format': "{stack}"
                    }}
                list_of_yaxes.append(yaxis_dict)

        bar_chart_data_multiyaxis = {
            'chart': {
                'type': 'column',
                'width': 1200,
                'height': plot_height,
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
            'yAxis': list_of_yaxes,
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
            "tooltip": {
                "pointFormat": "{series.name}: <b>${point.y:.2f}"
                "</b><br>{series.options.stack}<br>"
            }
        }
        User_totals_initial = ComputeCosts.objects.filter(
                project__name__startswith=project,
                date__date__range=[month_start, month_end]
                ).values('date__date__month',
                         'date__date__year',
                         'launched_by__user_name'
                         ).order_by('date__date__month'
                                    ).annotate(Cost=Sum('total_cost'))
        project_axis = -1
        for project in project_types:
            project_axis += 1
            for user in user_types:
                User_totals = ComputeCosts.objects.filter(
                project__name__startswith=project,
                launched_by__user_name__endswith = user,
                date__date__range=[month_start, month_end]
                ).values('date__date__month',
                         'date__date__year',
                         'launched_by__user_name'
                         ).order_by('date__date__month'
                                    ).annotate(Cost=Sum('total_cost'))
                data ={"name": f"{project} {user}",
                        "data": list(User_totals.values_list(
                            'date__date__month',
                            'Cost'  # , flat=True
                            )),
                        'yAxis': project_axis,
                    }
                category_data_source.append(data)
            category_chart_data = bar_chart_data_multiyaxis
            category_chart_data['xAxis']['categories'] = self.better_string_months
            category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_alldata_byproject_user(month_start,
                                                             month_end,
                                                             project_types,
                                                             user_types)

        return json_chart_data, chart_df


    def Monthly_allprojects(self, month_start, month_end, form):
        """
        WORKING EXAMPLE
        Displays the monthly cost for all projects for a monthly range.

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'leaderboard_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        category_data_source = []
        User_totals = ComputeCosts.objects.filter(
            date__date__range=[month_start, month_end]
            ).order_by('date__date__month'
                        ).values('date__date__month',
                                 'date__date__year',
                                 'launched_by__user_name'
                     ).annotate(Cost=Sum('total_cost'))
        string_users = set(self.get_users_as_str(User_totals))

        for user in string_users:
            data ={
                    "name": f"{user}",
                    "data": list(User_totals.filter(
                        launched_by__user_name__endswith = user).values_list(
                        'Cost', flat=True
                        ))
                    # 'color': 'rgb(217,95,2)'
                }

            category_data_source.append(data)

        category_chart_data = self.bar_chart_data.copy()
        category_chart_data['xAxis']['categories'] = self.better_string_months
        category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_alldata_default(month_start, month_end)

        return json_chart_data, chart_df


    def Monthly_byUsers(self, month_start,
                        month_end, user_types, form):
        """
        WORKING EXAMPLE
        Filters the data by monthly range and user and displays by months.

        Parameters
        ----------
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'leaderboard_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        category_data_source = []
        user_types = self.str_to_list(user_types)
        User_totals = ComputeCosts.objects.filter(
            date__date__range=[month_start, month_end]
            ).values('date__date__month',
                     'date__date__year',
                     'launched_by__user_name'
                     ).order_by('date__date__month'
                                ).annotate(Cost=Sum('total_cost'))

        # string_months = self.get_month_years_as_str(User_totals)

        for user in user_types:
            data ={
                    "name": f"{user}",
                    "data": list(User_totals.filter(
                        launched_by__user_name__endswith = user).values_list(
                        'Cost', flat=True
                        ))
                    # 'color': 'rgb(217,95,2)'
                }
            category_data_source.append(data)
        category_chart_data = self.bar_chart_data.copy()
        category_chart_data['xAxis']['categories'] = self.better_string_months
        category_chart_data['series'] = category_data_source

        json_chart_data = json.dumps(category_chart_data)

        chart_df = self.convert_to_df_alldata_by_user(month_start,
                                                      month_end,
                                                      user_types)

        return json_chart_data, chart_df


    def top_most_costly_job(self, month_start, month_end, form):
        """top_most_costly_job
        This function returns the top most costly job in the last 4 months.

        Returns:
            _type_: _description_

        """
        User_totals = ComputeCosts.objects.filter(
                date__date__range=[month_start, month_end]
                ).values('launched_by__user_name'
                         ).annotate(Cost=Sum('total_cost')
                                    ).order_by('Cost').latest('Cost')
        top_user = User_totals
        top_user_name = top_user['launched_by__user_name'].split("-")[1]
        top_user_cost = round(top_user['Cost'], 2)
        return top_user_name, top_user_cost

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


    def convert_to_df_timeseries(self, month_start, month_end, project_types):
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
                project__name__startswith=project,
                date__date__range=[month_start, month_end]
                ).values('dx_id',
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
                    'runtime': 'Runtime*'
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
        Queries the DB and converts data to a pandas df then convert it to HTML
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
                        'runtime': 'Runtime*'
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
        Queries the DB and converts data to a pandas df then convert it to HTML
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
                    'runtime': 'Runtime*'
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


    def convert_to_df_alldata_default(self, month_start,
                                     month_end):
        """
        Queries the DB and converts data to a pandas df then convert it to HTML
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

        cost_list = ComputeCosts.objects.all().filter(
            date__date__range=[month_start, month_end]
            ).values('dx_id',
                     'date__date',
                     'project__name',
                     'total_cost',
                     'launched_by__user_name',
                     'executable_name__executable_name',
                     'runtime', )
        cost_df = pd.DataFrame(cost_list)
        if not cost_df.empty:
            cost_df['launched_by__user_name'] = cost_df['launched_by__user_name'].apply(
                lambda x: x.split('-')[1])
            cost_df['total_cost'] = cost_df['total_cost'].apply(
                lambda x: round(x, 2))
            cost_df.rename(
                columns={
                    'dx_id': 'DNAnexus ID',
                    'date__date': 'Date',
                    'project__name': 'Project',
                    'Assay_type': 'Assay Type',
                    'total_cost': 'Total Cost ($)',
                    'launched_by__user_name': 'User',
                    'executable_name__executable_name': 'Executable',
                    'runtime': 'Runtime*'
                },
                inplace = True
            )
        # Convert to HTML to easily show with DataTables

        chart_data = cost_df.to_html(
            index=False,
            classes='table table-striped"',
            justify='left'
        )
        return chart_data


    def convert_to_df_alldata_by_project(self, month_start,
                                     month_end, project_types):
        """
        Queries the DB and converts data to a pandas df then convert it to HTML
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
            cost_list = ComputeCosts.objects.all().filter(
                project__name__startswith=project,
                date__date__range=[month_start, month_end]
                ).values('dx_id',
                         'date__date',
                         'project__name',
                         'total_cost',
                         'launched_by__user_name',
                         'executable_name__executable_name',
                         'runtime', )
            cost_df = pd.DataFrame(cost_list)
            if not cost_df.empty:
                cost_df['launched_by__user_name'] = cost_df['launched_by__user_name'].apply(
                    lambda x: x.split('-')[1])
                cost_df['total_cost'] = cost_df['total_cost'].apply(
                    lambda x: round(x, 2))
                cost_df.rename(
                    columns={
                        'dx_id': 'DNAnexus ID',
                        'date__date': 'Date',
                        'project__name': 'Project',
                        'Assay_type': 'Assay Type',
                        'total_cost': 'Total Cost ($)',
                        'launched_by__user_name': 'User',
                        'executable_name__executable_name': 'Executable',
                        'runtime': 'Runtime*'
                    },
                    inplace = True
                )
            dfObj = dfObj.append(cost_df)
        # Convert to HTML to easily show with DataTables

        chart_data = dfObj.to_html(
            index=False,
            classes='table table-striped"',
            justify='left'
        )
        return chart_data

    def convert_to_df_alldata_by_user(self, month_start,
                                     month_end, user_types):
        """
        Queries the DB and converts data to a pandas df then convert it to HTML
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
        for user in user_types:
            cost_list = ComputeCosts.objects.all().filter(
                launched_by__user_name__endswith=user,
                date__date__range=[month_start, month_end]
                ).values('dx_id',
                         'date__date',
                         'project__name',
                         'total_cost',
                         'launched_by__user_name',
                         'executable_name__executable_name',
                         'runtime', )
            cost_df = pd.DataFrame(cost_list)
            if not cost_df.empty:
                cost_df['launched_by__user_name'] = cost_df['launched_by__user_name'].apply(
                    lambda x: x.split('-')[1])
                cost_df['total_cost'] = cost_df['total_cost'].apply(
                    lambda x: round(x, 2))
                cost_df.rename(
                    columns={
                        'dx_id': 'DNAnexus ID',
                        'date__date': 'Date',
                        'project__name': 'Project',
                        'Assay_type': 'Assay Type',
                        'total_cost': 'Total Cost ($)',
                        'launched_by__user_name': 'User',
                        'executable_name__executable_name': 'Executable',
                        'runtime': 'Runtime*'
                    },
                    inplace = True
                )
            dfObj = dfObj.append(cost_df)
        # Convert to HTML to easily show with DataTables

        chart_data = dfObj.to_html(
            index=False,
            classes='table table-striped"',
            justify='left'
        )
        return chart_data


    def convert_to_df_alldata_byproject_user(self, month_start, month_end,
                                          project_types, user_types):
        """
        Queries the DB and converts data to a pandas df then convert it to HTML
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
            for user in user_types:
                cost_list = ComputeCosts.objects.all().filter(
                    project__name__startswith=project,
                    launched_by__user_name__endswith=user,
                    date__date__range=[month_start, month_end]
                ).values('dx_id',
                         'date__date',
                         'project__name',
                         'total_cost',
                         'launched_by__user_name',
                         'executable_name__executable_name',
                         'runtime')
                cost_df = pd.DataFrame(cost_list)
                if not cost_df.empty:
                    cost_df['launched_by__user_name'] = cost_df['launched_by__user_name'].apply(
                        lambda x: x.split('-')[1])
                    cost_df['total_cost'] = cost_df['total_cost'].apply(
                    lambda x: round(x, 2))
                    cost_df.rename(
                        columns={
                            'dx_id': 'DNAnexus ID',
                            'date__date': 'Date',
                            'project__name': 'Project',
                            'Assay_type': 'Assay Type',
                            'total_cost': 'Total Cost ($)',
                            'launched_by__user_name': 'User',
                            'executable_name__executable_name': 'Executable',
                            'runtime': 'Runtime*'
                        },
                        inplace = True
                    )
                    dfObj = dfObj.append(cost_df)

        # Convert to HTML to easily show with DataTables

        chart_data = dfObj.to_html(
            index=False,
            classes='table table-striped"',
            justify='left'
        )
        return chart_data
