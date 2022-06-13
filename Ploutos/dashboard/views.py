import datetime
import json
import plotly.express as px
import plotly.graph_objects as pgo

from django.db.models import Sum
from dashboard.forms import DateForm, StorageForm
from dashboard.models import (
    Users, Projects, Dates, DailyOrgRunningTotal, StorageCosts
)
from django.shortcuts import render


def index(request):
    """View to display running total charges via Plotly"""

    totals = DailyOrgRunningTotal.objects.all()

    # If the form is submitted
    if 'submit' in request.GET:
        form = DateForm(request.GET)
        # If the dates entered are validated fine
        if form.is_valid():
            # Get the data entered
            start = form.cleaned_data.get("start")
            end = form.cleaned_data.get("end")
            charge_type = form.cleaned_data.get("charge_type")

            # Filter totals to get desired date range
            if start:
                totals = totals.filter(
                    date__id__in = (
                        Dates.objects.filter(
                            date__range=[start, end]
                        ).values_list(
                            'id', flat=True
                        )
                    )
                )

                # If user wants to see all charge types, render whole graph
                if charge_type == 'All':
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

                # If a specific charge type chosen, set y_data accordingly
                else:
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
                
                # Update layout
                fig.update_layout(
                    title={
                        'font_size': 24,
                        'xanchor': 'center',
                        'x': 0.5
                })

                # Send to context
                chart = fig.to_html()
                context = {'chart': chart, 'form': form}
        else:
            # If form not valid
            # Display unfiltered graph for all dates and show errors
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
            context = {'chart': chart, 'form': form}
    else:
        # If form not submitted display all charges for all dates in db
        form = DateForm()

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
        context = {'chart': chart, 'form': form}

    return render(request, 'index.html', context)


def storage_chart(request):
    """
    Creates a bar chart grouped by month with each month having two bars
    Denoting live vs archived status
    Each bar is stacked with either project type
    Or assay type depending on the filters entered
    """

    # Get colour schemes from Plotly discrete colours
    project_colours = px.colors.qualitative.Set1
    assay_colours = px.colors.qualitative.Bold

    # Specify colours for specific types of projects or assays
    # So these don't change on different filtering
    proj_colour_dict = {
        '001': project_colours[0],
        '002': project_colours[1],
        '003': project_colours[2],
        '004': project_colours[3]
    }

    assay_colour_dict = {
        'CEN': assay_colours[0],
        'MYE': assay_colours[1],
        'TWE': assay_colours[2],
        'TSO500': assay_colours[3],
        'SNP': assay_colours[4],
        'CP': assay_colours[5],
        'WES': assay_colours[6],
        'FH': assay_colours[7],
    }

    # Find the months that exist in the db as categories for the graph as list
    month_categories = list(
        StorageCosts.objects.order_by().values_list(
            'date__date__month', flat=True
            ).distinct()
    )

    # Dictionary to convert integer month from database to named month
    date_conversion_dict = {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        12: 'December'
    }

    # Convert the integer months present in the db to strings
    string_months = [month if month not in date_conversion_dict
    else date_conversion_dict[month] for month in month_categories]

    # If the user has submitted the form
    if 'submit' in request.GET:
        form = StorageForm(request.GET)
        # If form is valid
        # i.e. not >1 entry in project_types and assay_types at same time
        if form.is_valid():
            year = form.cleaned_data.get('year')
            month = form.cleaned_data.get('month')
            
            # Initialise list of the series to pass to Highcharts
            category_data_source = []
            # If user wants to see all the months in the db
            if month == 'All':
                # If there are both a project type and assay type entered
                # Get the single string from each
                if (form.cleaned_data.get('project_type') and
                    form.cleaned_data.get('assay_type')):
                    project_type = form.cleaned_data.get('project_type')
                    assay_type = form.cleaned_data.get('assay_type')

                    # Filter by startswith project type and ends with assay type
                    # Group by all available months
                    # Sum by live vs archived
                    cost_list = StorageCosts.objects.filter(
                        project__name__startswith = project_type,
                        project__name__endswith = assay_type,
                        date__date__year = year
                        ).order_by().values(
                            'date__date__month'
                            ).annotate(
                                Live = Sum('unique_cost_live'),
                                Archived = Sum('unique_cost_archived')
                    )
                    
                    # Set name of series
                    # Get live values as list
                    # Colour with dict or if proj type not in dict make purple
                    live_data = {
                        'name': f"{project_type}*{assay_type}",
                        'data': list(
                            cost_list.values_list(
                                'Live', flat=True
                                )
                        ),
                        'stack': 'Live',
                        'color': proj_colour_dict.get(
                            project_type, 'purple'
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
                            'color': proj_colour_dict.get(
                                project_type, 'purple'
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
                            'categories': string_months
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
                
                else:
                    # If 'All' months selected and
                    # There are only projects searched for
                    if form.cleaned_data.get('project_type'):
                        # Remove all whitespace + start + end commas
                        # Split by commas and add each to new list
                        proj_string = form.cleaned_data.get('project_type')
                        proj_types = proj_string.strip(",").replace(
                            " ", ""
                            ).split(",")
                        
                        # Filter by 'startswith' for each searched project type
                        # For each proj add data to dict
                        for proj_type in proj_types:
                            cost_list = StorageCosts.objects.filter(
                                project__name__startswith = proj_type,
                                date__date__year = year
                            ).order_by().values(
                                'date__date__month'
                                ).annotate(
                                    Live = Sum('unique_cost_live'),
                                    Archived = Sum('unique_cost_archived')
                            )

                            live_data = {
                                'name': proj_type,
                                'data': list(
                                    cost_list.values_list(
                                        'Live', flat=True)
                                ),
                                'stack': 'Live',
                                'color': proj_colour_dict.get(
                                    proj_type, 'purple'
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
                                'color':proj_colour_dict.get(
                                    proj_type, 'purple'
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
                                'categories': string_months
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

                    # If all months only assay(s) searched for
                    # Strip start and end commas, remove whitespace
                    # Split on commas and add to list
                    elif form.cleaned_data.get('assay_type'):
                        assay_string = form.cleaned_data.get('assay_type')
                        assay_types = assay_string.strip(",").replace(
                            " ", ""
                            ).split(",")

                        # Filter by 'endswith' for each searched assay type
                        for assay_type in assay_types:
                            cost_list = StorageCosts.objects.filter(
                                project__name__endswith = assay_type,
                                date__date__year = year
                                ).order_by().values(
                                    'date__date__month'
                                    ).annotate(
                                        Live = Sum('unique_cost_live'),
                                        Archived = Sum('unique_cost_archived')
                                    )
                            
                            live_data = {
                                'name': assay_type,
                                'data': list(
                                    cost_list.values_list(
                                        'Live', flat=True
                                    )
                                ),
                                'stack': 'Live',
                                'color': assay_colour_dict.get(
                                    assay_type, 'red'
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
                                'color': assay_colour_dict.get(
                                    assay_type, 'red'
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
                                'categories': string_months
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
                    
                    else:
                        # If form is submitted
                        # But no assay type or project type is searched for
                        # And want to see all months
                        # Display all the projects grouped by available months
                        storage_totals = StorageCosts.objects.filter(
                            date__date__year = year
                            ).order_by().values(
                                'date__date__month'
                                ).annotate(
                                    Live = Sum('unique_cost_live'),
                                    Archived = Sum('unique_cost_archived')
                                )

                        # No need to loop over anything
                        category_data_source = [
                        {
                            "name": "All projects",
                            "data": list(storage_totals.values_list(
                                'Live', flat=True
                                )
                            ),
                            'stack': 'Live'
                        },
                        {
                            "name": "All projects",
                            "data": list(storage_totals.values_list(
                                'Archived', flat=True
                                )
                            ),
                            'stack': 'Archived',
                            'linkedTo': ':previous'
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
                                'categories': string_months
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
            # A specific month has been selected
            else:
                # Convert the integer month to a string
                converted_month = date_conversion_dict[int(month)]

                # If a project type and an assay type entered
                if (form.cleaned_data.get('project_type') and
                form.cleaned_data.get('assay_type')):
                    project_type = form.cleaned_data.get('project_type')
                    assay_type = form.cleaned_data.get('assay_type')

                    # Proj name starts wth project type and ends with assay type
                    # Filter for specific year and month
                    cost_list = StorageCosts.objects.filter(
                        project__name__startswith = project_type, project__name__endswith = assay_type,
                        date__date__year = year,
                        date__date__month = month
                        ).aggregate(
                            Live = Sum('unique_cost_live'),
                            Archived = Sum('unique_cost_archived')
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
                        'color': proj_colour_dict.get(
                            project_type, 'purple'
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
                        'color': proj_colour_dict.get(
                            project_type, 'purple'
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

                # A specific month with only project type(s)
                elif form.cleaned_data.get('project_type'):
                    proj_string = form.cleaned_data.get('project_type')
                    # Strip commas from start and end
                    # Remove whitespace, split into list on commas
                    proj_types = proj_string.strip(",").replace(
                        " ", ""
                        ).split(",")

                    for proj_type in proj_types:
                        cost_list = StorageCosts.objects.filter(
                            project__name__startswith = proj_type,
                            date__date__year = year,
                            date__date__month = month
                        ).aggregate(
                                Live = Sum('unique_cost_live'),
                                Archived= Sum('unique_cost_archived')
                            )
                        
                        # If empty, returns None which wasn't showing noData message
                        live = cost_list.get('Live')
                        if live:
                            live = [live]
                        else:
                            live = []

                        live_data = {
                            'name': proj_type,
                            'data': live,
                            'stack': 'Live',
                            'color' : proj_colour_dict.get(
                                proj_type, 'purple'
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
                            'linkedTo' : ':previous',
                            'color' : proj_colour_dict.get(
                                proj_type, 'purple'
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

                # A specific month with assay type(s)
                elif form.cleaned_data.get('assay_type'):
                    assay_string = form.cleaned_data.get('assay_type')
                    assay_types = assay_string.strip(",").replace(
                        " ", ""
                        ).split(",")

                    for assay_type in assay_types:
                        cost_list = StorageCosts.objects.filter(
                            project__name__endswith = assay_type,
                            date__date__year = year,
                            date__date__month = month
                        ).aggregate(
                                Live = Sum('unique_cost_live'),
                                Archived= Sum('unique_cost_archived')
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
                            'color' : assay_colour_dict.get(
                                assay_type, 'red'
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
                            'linkedTo' : ':previous',
                            'color': assay_colour_dict.get(
                                assay_type, 'red'
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
                
                else:
                    # If form submitted
                    # But no proj or assay type but specific year/month selected
                    # Because those fields are required
                    cost_list = StorageCosts.objects.filter(
                        date__date__year = year,
                        date__date__month=month
                    ).aggregate(
                        Live = Sum('unique_cost_live'),
                        Archived = Sum('unique_cost_archived')
                        )
                    
                    category_data_source = [
                        {
                            "name": "All projects",
                            "data": [cost_list.get('Live')],
                            'stack': 'Live'
                        },
                        {
                            'name': 'All projects',
                            'data': [cost_list.get('Archived')],
                            'stack': 'Archived',
                            'linkedTo': ':previous'
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

        else:
            # If the form is not valid, display just the standard graph
            # Of this year, grouped by available months
            # For all projects
            storage_totals = StorageCosts.objects.filter(
                date__date__year = '2022'
                ).order_by().values(
                    'date__date__month'
                    ).annotate(
                        Live = Sum('unique_cost_live'),
                        Archived=Sum('unique_cost_archived')
                        )

            category_data_source = [
            {
                "name": "All projects",
                "data": list(storage_totals.values_list(
                    'Live', flat=True
                    )
                 ),
                'stack': 'Live'
            },
            {
                "name": "All projects",
                "data": list(storage_totals.values_list(
                    'Archived', flat=True
                    )
                ),
                'stack': 'Archived',
                'linkedTo': ':previous'
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
                    'categories': string_months
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
    
    else:
        # If nothing is submitted on the form (normal landing page)
        # Display the all projects graph grouped by available months
        form = StorageForm()
        storage_totals = StorageCosts.objects.filter(
            date__date__year = '2022'
            ).order_by().values(
                'date__date__month'
                ).annotate(
                    Live = Sum('unique_cost_live'),
                    Archived = Sum('unique_cost_archived')
            )

        category_data_source = [
            {
                "name": "All projects",
                "data": list(storage_totals.values_list(
                    'Live', flat=True
                        )
                    ),
                'stack': 'Live'
            },

            {
                "name": "All projects",
                "data": list(storage_totals.values_list(
                    'Archived', flat=True
                    )
                ),
                'stack': 'Archived',
                'linkedTo': ':previous'
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
                'categories': string_months
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

    return render(request, 'bar_chart.html', context)

def jobs(request):
    """View to display the jobs data"""
    return render(request, 'jobs.html')
