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
                            date__range = [start, end]
                        ).values_list(
                            'id', flat = True
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
    """Grouped bar chart with project type + assay type filtering by month"""

    # Get colour schemes from plotly discrete colours
    project_colours = px.colors.qualitative.Set1
    assay_colours = px.colors.qualitative.Bold

    # Specify colours for specific types so these don't change after filtering
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

    # Find the months that exist in the db as categories for the graph
    month_categories = list(
        StorageCosts.objects.order_by().values_list(
            'date__date__month', flat = True
            ).distinct()
    )

    # Dict to convert integer month to named month
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

    # Convert the months present in the db
    string_months = [month if month not in date_conversion_dict
    else date_conversion_dict[month] for month in month_categories]

    if 'submit' in request.GET:
        form = StorageForm(request.GET)
        # If not >1 entry in project_types and assay_types at same time
        if form.is_valid():
            year = form.cleaned_data.get('year')
            month = form.cleaned_data.get('month')
            
            category_data_source = []
            # If user wants to see all the months in the db
            if month == 'All':
            
                # If there are both a project type and assay type entered
                # Validated to be only one of each so get the string from each
                if (form.cleaned_data.get('project_type') and
                    form.cleaned_data.get('assay_type')):
                    project_type = form.cleaned_data.get('project_type')
                    assay_type = form.cleaned_data.get('assay_type')

                    # Filter by startswith project type and ends with assay type
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
                    
                    live_data = {
                        'name': f"{project_type}*{assay_type}",
                        'data': list(
                            cost_list.values_list(
                                'Live', flat = True
                                )
                        ),
                        'stack': 'Live',
                        'color': proj_colour_dict.get(
                            project_type, 'purple'
                        )
                    }

                    archived_data = {
                            'name': f"{project_type}*{assay_type}",
                            'data': list(
                                cost_list.values_list(
                                    'Archived',flat=True
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
                    # If there are only projects searched for
                    if form.cleaned_data.get('project_type'):
                        # Remove all whitespace + add to list, split by commas
                        proj_string = form.cleaned_data.get('project_type')
                        proj_types = proj_string.strip(",").replace(
                            " ", ""
                            ).split(",")
                        
                        # Filter by 'startswith' for each searched project type
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
                                        'Live', flat = True)
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
                                        'Archived', flat = True)
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

                    # If there only assays searched for
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
                                    cost_list.values_list('Live', flat = True)
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
                                        'Archived',flat = True
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
                        # Display all the projects
                        storage_totals = StorageCosts.objects.filter(
                            date__date__year = year
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
                                'Live', flat = True
                                )
                            ),
                            'stack': 'Live'
                        },
                        {
                            "name": "All projects",
                            "data": list(storage_totals.values_list(
                                'Archived', flat = True
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
                # A specific month has been selected
                converted_month = date_conversion_dict[int(month)]

                # If a project type and an assay type entered
                if (form.cleaned_data.get('project_type') and
                form.cleaned_data.get('assay_type')):
                    project_type = form.cleaned_data.get('project_type')
                    assay_type = form.cleaned_data.get('assay_type')

                    cost_list = StorageCosts.objects.filter(
                        project__name__startswith = project_type, project__name__endswith = assay_type,
                        date__date__year = year,
                        date__date__month = month
                        ).aggregate(
                            Live = Sum('unique_cost_live'),
                            Archived = Sum('unique_cost_archived')
                        )
                    
                    # If empty, returns None which wasn't showing noData message
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

                    # If queryset empty, returns None
                    # This wasn't showing noData message
                    # This keeps data as list or if None converts to empty list
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

                # A specific month with project type(s)
                elif form.cleaned_data.get('project_type'):
                    
                    proj_string = form.cleaned_data.get('project_type')
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
                    # If no proj or assay type but specific year/month selected
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
                    'Live', flat = True
                    )
                 ),
                'stack': 'Live'
            },
            {
                "name": "All projects",
                "data": list(storage_totals.values_list(
                    'Archived', flat = True
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
        # Display all projects graph
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
                    'Live', flat = True
                        )
                    ),
                'stack': 'Live'
            },

            {
                "name": "All projects",
                "data": list(storage_totals.values_list(
                    'Archived', flat = True
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
