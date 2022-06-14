import json

from dashboard.models import StorageCosts
from django.db.models import Sum

def all_months_assay_type_and_proj_type(project_type, assay_type, year, project_colours, proj_colour_dict, string_months, form):
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
            project_type, project_colours[0]
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
                project_type, project_colours[0]
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

    return context

def all_months_only_project_types(proj_types, year, proj_colour_dict,
    project_colours, string_months, form):
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

        live_data = {
            'name': proj_type,
            'data': list(
                cost_list.values_list(
                    'Live', flat=True)
            ),
            'stack': 'Live',
            'color': proj_colour_dict.get(
                proj_type, project_colours[count]
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
                proj_type, project_colours[count]
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

    return context

def all_months_only_assay_types(assay_types, year, assay_colour_dict, assay_colours,
    string_months, form):
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
            'color': assay_colour_dict.get(
                assay_type, assay_colours[count]
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
                assay_type, assay_colours[count]
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

    return context

def all_months_form_submitted_no_proj_or_assay(year, string_months, form):

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

    return context

def specific_month_proj_and_assay(project_type, assay_type, year, month, proj_colour_dict, project_colours, converted_month, form):
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
        'color': proj_colour_dict.get(
            project_type, project_colours[0]
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
            project_type, project_colours[0]
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

def specific_month_only_proj_types(proj_types, year, month, proj_colour_dict, project_colours, converted_month, form):
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
                proj_type, project_colours[count]
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
            'color' : proj_colour_dict.get(
                proj_type, project_colours[count]
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

def specific_month_only_assay_types(assay_types, year, month, assay_colour_dict, assay_colours, converted_month, form):

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
            'color' : assay_colour_dict.get(
                assay_type, assay_colours[count]
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
            'color': assay_colour_dict.get(
                assay_type, assay_colours[count]
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

def specific_month_no_proj_or_assay(year, month, converted_month, form):
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

def form_is_not_valid(current_year, string_months, form):
    storage_totals = StorageCosts.objects.filter(
        date__date__year=current_year
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

    return context

def form_is_not_submitted(current_year, string_months, form):
    storage_totals = StorageCosts.objects.filter(
        date__date__year=current_year
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

    return context