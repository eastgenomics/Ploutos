"""This script holds plotting functions used in views.py"""

import json
import plotly.express as px
import plotly.graph_objects as pgo

from dashboard.models import StorageCosts, DailyOrgRunningTotal
from django.conf import settings
from django.db.models import Sum
from scripts import DNAnexus_queries as q
from scripts import date_conversion as dc

class RunningTotPlotFunctions():
    """Class for plotting functions for the running total graph"""

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

        compute = [c.compute_charges for c in totals]
        storage = [c.storage_charges for c in totals]
        egress = [c.egress_charges for c in totals]
        fig = px.line(
            x=[x.date.date for x in totals],
            y=compute,
            title="Running charges",
            labels={
                'x': 'Date',
                'y': 'Charges ($)'
            },
            width=1200,
            height=600
        )

        fig.data[0].name = "Compute"
        fig.update_traces(showlegend=True)
        fig.add_scatter(
            x=[x.date.date for x in totals],
            y=storage,
            mode='lines',
            name="Storage"
        )
        fig.add_scatter(
            x=[x.date.date for x in totals],
            y=egress,
            mode='lines',
            name="Egress"
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

        if charge_type == "Egress":
            y_data = [c.egress_charges for c in totals]
            updated_title = "Egress running total charges"
            colour = '#00CC96'
        elif charge_type == "Compute":
            y_data = [c.compute_charges for c in totals]
            updated_title = "Compute running total charges"
            colour = '#EF553B'
        elif charge_type == "Storage":
            y_data = [c.storage_charges for c in totals]
            updated_title = "Storage running total charges"
            colour = '#636EFA'

        fig = px.line(
            x=[x.date.date for x in totals],
            y=y_data,
            title=updated_title,
            labels={
                'x': 'Date',
                'y': 'Charges ($)'
            },
            width=1200,
            height=600
        )
        # Set the colour so it's the same as on the all charges plot
        fig['data'][0]['line']['color'] = colour

        return fig

    def totals_form_not_valid(self, totals, form):
        """
        Set context when the form is not valid (wrong dates)
        Parameters
        ----------
        totals :  queryset
            queryset already filtered by the specified daterange
        form : Django form object
            form either as Form(request.GET) or Form()
        Returns
        -------
        context : dict
            context to pass to HTML

        """
        totals = DailyOrgRunningTotal.objects.all()
        compute = [c.compute_charges for c in totals]
        storage = [c.storage_charges for c in totals]
        egress = [c.egress_charges for c in totals]
        fig = px.line(
            x=[x.date.date for x in totals],
            y=compute,
            title="Running total charges",
            labels={
                'x': 'Date',
                'y': 'Charges ($)'
            },
            width=1200,
            height=600
        )

        # Add all scatters and update legend labels
        fig.data[0].name = "Compute"
        fig.update_traces(showlegend=True)
        fig.add_scatter(
            x=[x.date.date for x in totals],
            y=storage,
            mode='lines',
            name='Storage'
        )

        fig.add_scatter(
            x=[x.date.date for x in totals],
            y=egress,
            mode='lines',
            name='Egress'
        )

        # Change formatting of title
        fig.update_layout(
            title={
                'font_size': 24,
                'xanchor': 'center',
                'x': 0.5
            }
        )

        chart = fig.to_html()
        context = {
            'chart': chart,
            'form': form
        }

        return context

    def form_not_submitted(self, totals, form):
        """
        Set context when the form is not submitted
        Includes all dates present in db and all charge types
        Parameters
        ----------
        totals :  queryset
            queryset already filtered by the specified daterange
        form : Django form object
            form either as Form(request.GET) or Form()
        Returns
        -------
        context : dict
            context to pass to HTML
        
        """
        # Plot the date and storage charges as line graph
        totals = DailyOrgRunningTotal.objects.all()
        compute = [c.compute_charges for c in totals]
        storage = [c.storage_charges for c in totals]
        egress = [c.egress_charges for c in totals]
        fig = px.line(
            x=[x.date.date for x in totals],
            y=compute,
            title="Running total charges",
            labels={
                'x':'Date',
                'y':'Charges ($)'
            },
            width=1200,
            height=600
        )

        fig.data[0].name = "Compute"
        fig.update_traces(showlegend=True)
        fig.add_scatter(
            x=[x.date.date for x in totals],
            y=storage,
            mode='lines',
            name="Storage"
        )
        fig.add_scatter(
            x=[x.date.date for x in totals],
            y=egress,
            mode='lines',
            name="Egress"
        )

        # Change formatting of title
        fig.update_layout(
            title={
                'font_size': 24,
                'xanchor': 'center',
                'x': 0.5
            }
        )

        chart = fig.to_html()
        context = {
            'chart': chart,
            'form': form
        }

        return context


class StoragePlotFunctions():
    """Class for all of the storage plotting functions"""

    # Get current year
    current_year = q.no_of_days_in_month()[0].split('-')[0]

    # Get colour schemes from Plotly discrete colours
    project_colours = px.colors.qualitative.Set1
    assay_colours = px.colors.qualitative.Bold

    # Specify colours for specific types of projects or assays
    # So these don't change on diff numbers of types/assays during filtering
    # Gets from the config file
    proj_colour_dict = settings.PROJ_COLOUR_DICT
    assay_colour_dict = settings.ASSAY_COLOUR_DICT

    # Find the months that exist in the db as categories for the graph as list
    month_categories = list(
        StorageCosts.objects.order_by().values_list(
            'date__date__month', flat=True
            ).distinct()
        )

    # Convert the integer months present in the db to strings
    # Importing the date conversion dict because for some reason Python
    # Wouldn't find it even though it's literally defined above ?
    string_months = [month if month not in dc.date_conversion_dict
    else dc.date_conversion_dict[month] for month in month_categories]

    def all_months_assay_type_and_proj_type(self, project_type, assay_type,
        year, form):
        """
        Sets context when 'All' months are selected, with one project type
        And one assay type

        Parameters
        ----------
        project type :  str
            string that the project name begins with
        assay type : str
            string that the project name ends with
        year : str
            year that the date of the objects should belong to
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'storage_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """

        category_data_source = []
        # Filter by startswith project type and ends with assay type
        # Group by all available months
        # Sum by live vs archived
        cost_list = StorageCosts.objects.filter(
            project__name__startswith=project_type,
            project__name__endswith=assay_type,
            date__date__year = year
            ).order_by().values(
                'date__date__month'
                ).annotate(
                    Live=Sum('unique_cost_live'),
                    Archived=Sum('unique_cost_archived')
        )

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
        category_chart_data = {
            'chart': {
                'type': 'column',
                'width': 1200,
                'height': 500,
                'style': {
                    'float': 'center'
                }
            },
            'title': {
                'text': 'Storage Costs'
            },
            'xAxis': {
                'categories': self.string_months
            },
            'yAxis': {
                'allowDecimals': 'false',
                'min': '0',
                'title': {
                    'text': 'Total estimated storage cost ($)'
                },
                'stackLabels': {
                    'enabled': 'true',
                    'allowOverlap':'true',
                    'style': {
                        'fontWeight': 'bold',
                        'color': 'gray'
                    },
                    'format': "{stack}"
                }
            }
            ,
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
            'series': category_data_source
        }

        context = {
        'storage_data': json.dumps(category_chart_data),
        'form': form
        }

        return context

    def all_months_only_project_types(self, proj_types, year, form):
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
            'storage_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # Filter by 'startswith' for each searched project type
        # For each proj add data to dict
        category_data_source = []
        count = -1
        for proj_type in proj_types:
            count+=1
            cost_list = StorageCosts.objects.filter(
                project__name__startswith=proj_type,
                date__date__year=year
            ).order_by().values(
                'date__date__month'
                ).annotate(
                    Live=Sum('unique_cost_live'),
                    Archived=Sum('unique_cost_archived')
            )

            # Either get bar colour from dict or iterate through project_colours
            live_data = {
                'name': proj_type,
                'data': list(
                    cost_list.values_list(
                        'Live', flat=True)
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
                        'Archived', flat=True)
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

        category_chart_data = {
            'chart': {
                'type': 'column',
                'width': 1200,
                'height': 500,
                'style': {
                    'float': 'center'
                }
            },
            'title': {
                'text': 'Storage Costs'
            },
            'xAxis': {
                'categories': self.string_months
            },
            'yAxis': {
                'allowDecimals': 'false',
                'min': '0',
                'title': {
                    'text': 'Total estimated storage cost ($)'
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
            }
            ,
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
            'series': category_data_source
        }

        context = {
            'storage_data': json.dumps(category_chart_data),
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
            'storage_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        category_data_source = []
        # Filter by 'endswith' for each searched assay type
        count = -1
        for assay_type in assay_types:
            count+=1
            cost_list = StorageCosts.objects.filter(
                project__name__endswith=assay_type,
                date__date__year=year
                ).order_by().values(
                    'date__date__month'
                    ).annotate(
                        Live=Sum('unique_cost_live'),
                        Archived=Sum('unique_cost_archived')
                    )
            
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

        category_chart_data = {
            'chart': {
                'type': 'column',
                'width': 1200,
                'height': 500,
                'style': {
                    'float': 'center'
                }
            },
            'title': {
                'text': 'Storage Costs'
            },
            'xAxis': {
                'categories': self.string_months
            },
            'yAxis': {
                'allowDecimals': 'false',
                'min': '0',
                'title': {
                    'text': 'Total estimated storage cost ($)'
                },
                'stackLabels': {
                    'enabled': 'true',
                    'allowOverlap':'true',
                    'style': {
                        'fontWeight': 'bold',
                        'color': 'gray'
                    },
                    'format': "{stack}"
                }
            }
            ,
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
            'series': category_data_source
        }

        context = {
            'storage_data': json.dumps(category_chart_data),
            'form': form
        }

        return context

    def all_months_form_submitted_no_proj_or_assay(self, year, form):
        """
        Sets context when 'All' months selected
        But no project types or assay types (only year + month)

        Parameters
        ----------
        year : str
            year that the date of the objects should belong to
        form : Django form object
            the related Django form in forms.py

        Returns
        -------
        context : dict
            'storage_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        storage_totals = StorageCosts.objects.filter(
        date__date__year=year
        ).order_by().values(
            'date__date__month'
            ).annotate(
                Live=Sum('unique_cost_live'),
                Archived=Sum('unique_cost_archived')
            )

        # No need to loop over anything
        category_data_source = [
        {
            "name": "All projects",
            "data": list(storage_totals.values_list(
                'Live', flat=True
                )
            ),
            'stack': 'Live',
            'color': 'rgb(217,95,2)'
        },
        {
            "name": "All projects",
            "data": list(storage_totals.values_list(
                'Archived', flat=True
                )
            ),
            'stack': 'Archived',
            'linkedTo': ':previous',
            'color': 'rgb(217,95,2)',
            'opacity': 0.8
        }
        ]

        category_chart_data = {
            'chart': {
                'type': 'column',
                'width': 1200,
                'height': 500,
                'style': {
                    'float': 'center'
                }
            },
            'title': {
                'text': 'Storage Costs'
            },
            'xAxis': {
                'categories': self.string_months
            },
            'yAxis': {
                'allowDecimals': 'false',
                'min': '0',
                'title': {
                    'text': 'Total estimated storage cost ($)'
                },
                'stackLabels': {
                    'enabled': 'true',
                    'allowOverlap':'true',
                    'style': {
                        'fontWeight': 'bold',
                        'color': 'gray'
                    },
                    'format': "{stack}"
                }
            }
            ,
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
            'series': category_data_source
        }

        context = {
            'storage_data': json.dumps(category_chart_data),
            'form': form
        }

        return context

    def specific_month_proj_and_assay(self, project_type, assay_type, year,
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
            'storage_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        category_data_source = []
        # Proj name starts wth project type and ends with assay type
        # Filter for specific year and month
        cost_list = StorageCosts.objects.filter(
            project__name__startswith=project_type,
            project__name__endswith=assay_type,
            date__date__year=year,
            date__date__month=month
            ).aggregate(
                Live=Sum('unique_cost_live'),
                Archived=Sum('unique_cost_archived')
            )
        
        # Get the live aggregate for those projects
        # If QS empty, returns None which affects noData message
        # Keep as list with actual data or convert [None] to []
        live = cost_list.get('Live')
        if live:
            live = [live]
        else:
            live = []

        live_data = {
            'name': f"{project_type}*{assay_type}",
            'data': live,
            'stack': 'Live',
            'color': self.proj_colour_dict.get(
                project_type, self.project_colours[0]
            )
        }

        # Get the archived aggregate for those projects
        # If QS empty, returns None which affects noData message
        # Keep as list with actual data or convert [None] to []
        archived = cost_list.get('Archived')
        if archived:
            archived = [archived]
        else:
            archived = []

        archived_data = {
            'name': f"{project_type}*{assay_type}",
            'data': archived,
            'stack': 'Archived',
            'linkedTo': ':previous',
            'color': self.proj_colour_dict.get(
                project_type, self.project_colours[0]
            ),
            'opacity': 0.8
        }

        category_data_source.append(live_data)
        category_data_source.append(archived_data)

        # As only one series, categories must be a list
        # Or Highcharts bug means it
        # Only shows the first letter of the category
        category_chart_data = {
            'chart': {
                'type': 'column',
                'width': 1200,
                'height': 500,
                'style': {
                    'float': 'center'
                }
            },
            'title': {
                'text': 'Storage Costs'
            },
            'xAxis': {
                'categories': [converted_month]
            },
            'yAxis': {
                'allowDecimals': 'false',
                'min': '0',
                'title': {
                    'text': 'Total estimated storage cost ($)'
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
            }
            ,
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
            'series': category_data_source
        }
        
        context = {
            'storage_data': json.dumps(category_chart_data),
            'form': form
        }

        return context

    def specific_month_only_proj_types(self, proj_types, year, month,
        converted_month, form
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
            'storage_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        # Increase count per proj_type to assign new colours to bars
        category_data_source = []
        count=-1
        for proj_type in proj_types:
            count+=1
            cost_list = StorageCosts.objects.filter(
                project__name__startswith=proj_type,
                date__date__year=year,
                date__date__month=month
            ).aggregate(
                    Live=Sum('unique_cost_live'),
                    Archived=Sum('unique_cost_archived')
                )
            
            live = cost_list.get('Live')
            # If empty, returns None which wasn't showing noData message
            # Converted to empty list instead if [None]
            if live:
                live = [live]
            else:
                live = []

            live_data = {
                'name': proj_type,
                'data': live,
                'stack': 'Live',
                'color' : self.proj_colour_dict.get(
                    proj_type, self.project_colours[count]
                )
            }

            archived = cost_list.get('Archived')
            if archived:
                archived = [archived]
            else:
                archived = []

            archived_data = {
                'name' : proj_type,
                'data': archived,
                'stack': 'Archived',
                'linkedTo': ':previous',
                'color' : self.proj_colour_dict.get(
                    proj_type, self.project_colours[count]
                ),
                'opacity': 0.8
            }

            category_data_source.append(live_data)
            category_data_source.append(archived_data)

        
        category_chart_data = {
            'chart': {
                'type': 'column',
                'width': 1200,
                'height': 500,
                'style': {
                    'float': 'center'
                }
            },
            'title': {
                'text': 'Storage Costs'
            },
            'xAxis': {
                'categories': [converted_month]
            },
            'yAxis': {
                'allowDecimals': 'false',
                'min': '0',
                'title': {
                    'text': 'Total estimated storage cost ($)'
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
            }
            ,
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
            'series': category_data_source
        }

        context = {
            'storage_data': json.dumps(category_chart_data),
            'form': form
        }

        return context

    def specific_month_only_assay_types(self, assay_types, year, month,
        converted_month, form
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
            'storage_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        category_data_source = []
        count=-1
        for assay_type in assay_types:
            count+=1
            cost_list = StorageCosts.objects.filter(
                project__name__endswith=assay_type,
                date__date__year=year,
                date__date__month=month
            ).aggregate(
                    Live=Sum('unique_cost_live'),
                    Archived=Sum('unique_cost_archived')
                )

            live = cost_list.get('Live')
            if live:
                live = [live]
            else:
                live = []

            live_data = {
                'name': assay_type,
                'data': live,
                'stack': 'Live',
                'color' : self.assay_colour_dict.get(
                    assay_type, self.assay_colours[count]
                )
            }

            archived = cost_list.get('Archived')
            if archived:
                archived = [archived]
            else:
                archived = []
            
            archived_data = {
                'name' : assay_type,
                'data': archived,
                'stack': 'Archived',
                'linkedTo': ':previous',
                'color': self.assay_colour_dict.get(
                    assay_type, self.assay_colours[count]
                ),
                'opacity': 0.8
            }
        

            category_data_source.append(live_data)
            category_data_source.append(archived_data)

        
        category_chart_data = {
            'chart': {
                'type': 'column',
                'width': 1200,
                'height': 500,
                'style': {
                    'float': 'center'
                }
            },
            'title': {
                'text': 'Storage Costs'
            },
            'xAxis': {
                'categories': [converted_month]
            },
            'yAxis': {
                'allowDecimals': 'false',
                'min': '0',
                'title': {
                    'text': 'Total estimated storage cost ($)'
                },
                'stackLabels': {
                    'enabled': 'true',
                    'allowOverlap':'true',
                    'style': {
                        'fontWeight': 'bold',
                        'color': 'gray'
                    },
                    'format': "{stack}"
                }
            }
            ,
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
            'series': category_data_source
        }

        context = {
            'storage_data': json.dumps(category_chart_data),
            'form': form
        }

        return context

    def specific_month_no_proj_or_assay(self, year, month, converted_month,
        form):
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
            'storage_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        cost_list = StorageCosts.objects.filter(
            date__date__year=year,
            date__date__month=month
        ).aggregate(
            Live=Sum('unique_cost_live'),
            Archived=Sum('unique_cost_archived')
            )
        
        category_data_source = [
            {
                "name": "All projects",
                "data": [cost_list.get('Live')],
                'stack': 'Live',
                'color': 'rgb(217,95,2)'
            },
            {
                'name': 'All projects',
                'data': [cost_list.get('Archived')],
                'stack': 'Archived',
                'linkedTo': ':previous',
                'color': 'rgb(217,95,2)',
                'opacity': 0.8
            }
        ]

        category_chart_data = {
            'chart': {
                'type': 'column',
                'width': 1200,
                'height': 500,
                'style': {
                    'float': 'center'
                }
            },
            'title': {
                'text': 'Storage Costs'
            },
            'xAxis': {
                'categories': [converted_month]
            },
            'yAxis': {
                'allowDecimals': 'false',
                'min': '0',
                'title': {
                    'text': 'Total estimated storage cost ($)'
                },
                'stackLabels': {
                    'enabled': 'true',
                    'allowOverlap':'true',
                    'style': {
                        'fontWeight': 'bold',
                        'color': 'gray'
                    },
                    'format': "{stack}"
                }
            }
            ,
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
            'series': category_data_source
        }

        context = {
            'storage_data': json.dumps(category_chart_data),
            'form': form
        }

        return context

    def form_is_not_valid(self, form):
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
            'storage_data': data to pass to Highcharts,
            'form': the form to pass to HTML
        """
        storage_totals = StorageCosts.objects.filter(
            date__date__year=self.current_year
            ).order_by().values(
                'date__date__month'
                ).annotate(
                    Live=Sum('unique_cost_live'),
                    Archived=Sum('unique_cost_archived')
                    )

        category_data_source = [
        {
            "name": "All projects",
            "data": list(storage_totals.values_list(
                'Live', flat=True
                )
                ),
            'stack': 'Live',
            'color': 'rgb(217,95,2)'
        },
        {
            "name": "All projects",
            "data": list(storage_totals.values_list(
                'Archived', flat=True
                )
            ),
            'stack': 'Archived',
            'linkedTo': ':previous',
            'color': 'rgb(217,95,2)',
            'opacity': 0.8
        }
        ]

        category_chart_data = {
            'chart': {
                'type': 'column',
                'width': 1200,
                'height': 500,
                'style': {
                    'float': 'center'
                }
            },
            'title': {
                'text': 'Storage Costs'
            },
            'xAxis': {
                'categories': self.string_months
            },
            'yAxis': {
                'allowDecimals': 'false',
                'min': '0',
                'title': {
                    'text': 'Total estimated storage cost ($)'
                },
                'stackLabels': {
                    'enabled': 'true',
                    'allowOverlap':'true',
                    'style': {
                        'fontWeight': 'bold',
                        'color': 'gray'
                    },
                    'format': "{stack}"
                }
            }
            ,
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
            'series': category_data_source
        }

        context = {
            'storage_data': json.dumps(category_chart_data),
            'form': form
        }

        return context

    def form_is_not_submitted(self, form):
        """
        Sets context for the landing page where no form is submitted
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
            date__date__year=self.current_year
            ).order_by().values(
                'date__date__month'
                ).annotate(
                    Live=Sum('unique_cost_live'),
                    Archived=Sum('unique_cost_archived')
            )

        category_data_source = [
            {
                "name": "All projects",
                "data": list(storage_totals.values_list(
                    'Live', flat=True
                        )
                    ),
                'stack': 'Live',
                'color': 'rgb(217,95,2)'
            },

            {
                "name": "All projects",
                "data": list(storage_totals.values_list(
                    'Archived', flat=True
                    )
                ),
                'stack': 'Archived',
                'linkedTo': ':previous',
                'color': 'rgb(217,95,2)',
                'opacity': 0.8
            }
        ]

        category_chart_data = {
            'chart': {
                'type': 'column',
                'width': 1200,
                'height': 500,
                'style': {
                    'float': 'center'
                }
            },
            'title': {
                'text': 'Storage Costs'
            },
            'xAxis': {
                'categories': self.string_months
            },
            'yAxis': {
                'allowDecimals': 'false',
                'min': '0',
                'title': {
                            'text': 'Total estimated storage cost ($)'
                },
                'stackLabels': {
                    'enabled': 'true',
                    'allowOverlap':'true',
                    'style': {
                        'fontWeight': 'bold',
                        'color': 'gray'
                    },
                    'format': "{stack}"
                }
            }
            ,
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
            'series': category_data_source
        }

        context = {
                'storage_data': json.dumps(category_chart_data),
                'form': form
        }

        return context