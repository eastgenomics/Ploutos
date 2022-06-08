from django.shortcuts import render
from django.db.models import Sum
import plotly.graph_objects as pgo
import plotly.express as px
from dashboard.forms import DateForm, StorageForm
from dashboard.models import Users, Projects, Dates, DailyOrgRunningTotal, StorageCosts
import datetime
import json


def index(request):
    """ 
    View to display running total charges via Plotly 
    """
    totals = DailyOrgRunningTotal.objects.all()

    # If the form is submitted
    if 'submit' in request.GET:
        form = DateForm(request.GET)
        # If the dates entered are fine
        if form.is_valid():
            print("Form is valid")
            # Get the data entered
            start = form.cleaned_data.get("start")
            end = form.cleaned_data.get("end")
            charge_type = form.cleaned_data.get("charge_type")

            # Filter totals to get desired date range
            if start:
                totals = totals.filter(date__id__in = (
                    Dates.objects.filter(date__range=[start,end]
                    ).values_list('id',flat=True)))

                # If want to see all charge types, render whole graph
                if charge_type == 'All':
                    compute = [c.compute_charges for c in totals]
                    storage = [c.storage_charges for c in totals]
                    egress = [c.egress_charges for c in totals]
                    fig = px.line(
                        x= [x.date.date for x in totals],
                        y=compute,
                        title = "Running charges",
                        labels = {'x':'Date', 'y':'Charges ($)'}, width=1200, height=600
                    )

                    fig.data[0].name = "Compute"
                    fig.update_traces(showlegend=True)
                    fig.add_scatter(x=[x.date.date for x in totals], y=storage, mode='lines', name="Storage")
                    fig.add_scatter(x=[x.date.date for x in totals], y=egress, mode='lines', name="Egress")

                # If not all charges, set y_data to be specific charge type
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
                        x = [x.date.date for x in totals],
                        y = y_data,
                        title = updated_title,
                        labels = {'x':'Date', 'y':'Charges ($)'}, width=1200, height=600
                    )
                    fig['data'][0]['line']['color']= colour
                
                # Update layout for all versions of graph
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
            # Render whole graph and display errors
            totals = DailyOrgRunningTotal.objects.all()
            compute = [c.compute_charges for c in totals]
            storage = [c.storage_charges for c in totals]
            egress = [c.egress_charges for c in totals]
            fig = px.line(
                x= [x.date.date for x in totals],
                y=compute,
                title = "Running total charges",
                labels = {'x':'Date', 'y':'Charges ($)'}, width=1200, height=600
            )

            # Legend labels weren't working so added new traces with names
            fig.data[0].name = "Compute"
            fig.update_traces(showlegend=True)
            fig.add_scatter(x=[x.date.date for x in totals], y=storage, mode='lines', name="Storage")
            fig.add_scatter(x=[x.date.date for x in totals], y=egress, mode='lines', name="Egress")

            # Change formatting of title
            fig.update_layout(
                title={
                    'font_size': 24,
                    'xanchor': 'center',
                    'x': 0.5
            })

            chart = fig.to_html()
            context = {'chart': chart, 'form': form}
    else:
        # If form not submitted render whole graph
        form = DateForm()

        # Plot the date and storage charges as line graph
        totals = DailyOrgRunningTotal.objects.all()
        compute = [c.compute_charges for c in totals]
        storage = [c.storage_charges for c in totals]
        egress = [c.egress_charges for c in totals]
        fig = px.line(
            x= [x.date.date for x in totals],
            y=compute,
            title = "Running total charges",
            labels = {'x':'Date', 'y':'Charges ($)'}, width=1200, height=600
        )

        # Legend labels weren't working so added new traces with names
        fig.data[0].name = "Compute"
        fig.update_traces(showlegend=True)
        fig.add_scatter(x=[x.date.date for x in totals], y=storage, mode='lines', name="Storage")
        fig.add_scatter(x=[x.date.date for x in totals], y=egress, mode='lines', name="Egress")

        # Change formatting of title
        fig.update_layout(
            title={
                'font_size': 24,
                'xanchor': 'center',
                'x': 0.5
        })

        chart = fig.to_html()
        context = {'chart': chart, 'form': form}
    return render(request, 'index.html', context)


def storage_chart(request):
    """Grouped bar chart with project type, assay type filtering grouped by month"""

    project_colours = px.colors.qualitative.Set1
    assay_colours = px.colors.qualitative.D3#

    proj_colour_dict = {'001': project_colours[0], '002': project_colours[1], '003': project_colours[2], '004': project_colours[3]}
    
    assay_colour_dict = {'CEN': assay_colours[0], 'MYE': assay_colours[1], 'TWE': assay_colours[2], 'TSO500': assay_colours[3],
    'SNP': assay_colours[4], 'CP': assay_colours[5], 'WES': assay_colours[6], 'FH':assay_colours[7]}

    # Find the months that exist in the db as categories 
    month_categories = list(StorageCosts.objects.order_by().values_list('date__date__month',flat=True).distinct())

    # Dict to convert integer month to named month
    date_conversion_dict = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}

    # Convert the months present in the db
    string_months = [x if x not in date_conversion_dict else date_conversion_dict[x] for x in month_categories]

    if 'submit' in request.GET:
        form = StorageForm(request.GET)
        # If only one type of filter is check-boxed
        if form.is_valid():
            print("Form is valid")
            category_data_source = []

            # If there are projects selected
            if form.cleaned_data.get('project_type'):
                proj_types = form.cleaned_data.get('project_type')
                count=-1
                
                # Filter by 'startswith' for each box-checked project type
                for proj_type in proj_types:
                    cost_list = StorageCosts.objects.filter(project__name__startswith= proj_type).order_by().values('date__date__month').annotate(Live = Sum('unique_cost_live'), Archived=Sum('unique_cost_archived'))
                    count+=1
                    live_data = {'name': proj_type, 'data': list(cost_list.values_list('Live',flat=True)), 'stack': 'Live', 'color': proj_colour_dict[proj_type]}
                    category_data_source.append(live_data)
                    archived_data = {'name': proj_type, 'data': list(cost_list.values_list('Archived',flat=True)), 'stack': 'Archived', 'linkedTo': ':previous', 'color': proj_colour_dict[proj_type]}
                    category_data_source.append(archived_data)

                    category_chart_data = {
                    'chart': {'type': 'column', 'width': 1200,
                    'height': 500, 'style': {
                    'float': 'center'
                    }},
                    'title': {'text': 'Storage Costs'},
                    'xAxis': {  	
                    'categories': string_months},
                    'yAxis': {'allowDecimals': 'false',
                        'min': '0',
                        'title': {
                            'text': 'Total cost'
                        },
                        'stackLabels': {
                            'enabled': 'true',
                            'allowOverlap':'true',
                            'style': {
                                'fontWeight': 'bold',
                                'color': 'gray',
                                'fontSize' : '12px'
                            }, 'format': "{stack}"
                        }}
                    ,
                    'setOptions': {
                        'lang': {
                            'thousandsSep': ','
                        }
                    },
                    'plotOptions': {'column': {'stacking': 'normal'}},
                    'series': category_data_source
                    }

                    context = {
                    'storage_data': json.dumps(category_chart_data),
                    'form': form}
            
            elif form.cleaned_data.get('assay_type'):
                # If there are assays selected
                assay_types = form.cleaned_data.get('assay_type')
                print("Assays selected")
                count = -1

                # Filter by 'endswith' for each box-checked assay type
                for assay_type in assay_types:
                    cost_list = StorageCosts.objects.filter(project__name__endswith= assay_type).order_by().values('date__date__month').annotate(Live = Sum('unique_cost_live'), Archived=Sum('unique_cost_archived'))
                    live_data = {'name': assay_type, 'data': list(cost_list.values_list('Live',flat=True)), 'stack': 'Live', 'color': assay_colour_dict[assay_type]}
                    category_data_source.append(live_data)
                    archived_data = {'name': assay_type, 'data': list(cost_list.values_list('Archived',flat=True)), 'stack': 'Archived', 'linkedTo': ':previous', 'color': assay_colour_dict[assay_type]}
                    category_data_source.append(archived_data)

                    category_chart_data = {
                    'chart': {'type': 'column', 'width': 1200,
                    'height': 500, 'style': {
                    'float': 'center'
                    }},
                    'title': {'text': 'Storage Costs'},
                    'xAxis': {  	
                    'categories': string_months},
                    'yAxis': {'allowDecimals': 'false',
                        'min': '0',
                        'title': {
                            'text': 'Total cost'
                        },
                        'stackLabels': {
                            'enabled': 'true',
                            'allowOverlap':'true',
                            'style': {
                                'fontWeight': 'bold',
                                'color': 'gray',
                                'fontSize' : '12px'
                            }, 'format': "{stack}"
                        }}
                    ,
                    'setOptions': {
                        'lang': {
                            'thousandsSep': ','
                        }
                    },
                    'plotOptions': {'column': {'stacking': 'normal'}},
                    'series': category_data_source
                    }

                    context = {
                    'storage_data': json.dumps(category_chart_data),
                    'form': form}
            else:
                storage_totals = StorageCosts.objects.order_by().values('date__date__month').annotate(Live = Sum('unique_cost_live'), Archived=Sum('unique_cost_archived'))

                category_data_source = [{"name": "All projects", "data": list(storage_totals.values_list('Live',flat=True)), 'stack': 'Live'}, {"name": "All projects", "data": list(storage_totals.values_list('Archived',flat=True)), 'stack': 'Archived', 'linkedTo': ':previous'}]

                category_chart_data = {
                'chart': {'type': 'column', 'width': 1200,
                'height': 500, 'style': {
                'float': 'center'
                }},
                'title': {'text': 'Storage Costs'},
                'xAxis': {  	
                'categories': string_months},
                'yAxis': {'allowDecimals': 'false',
                    'min': '0',
                    'title': {
                        'text': 'Total cost'
                    },
                    'stackLabels': {
                        'enabled': 'true',
                        'allowOverlap':'true',
                        'style': {
                            'fontWeight': 'bold',
                            'color': 'gray',
                            'fontSize' : '12px'
                        }, 'format': "{stack}"
                    }}
                ,
                'setOptions': {
                    'lang': {
                        'thousandsSep': ','
                    }
                },
                'plotOptions': {'column': {'stacking': 'normal'}},
                'series': category_data_source
                }

                context = {
                'storage_data': json.dumps(category_chart_data),
                'form': form}
    

        else:
            # The form is not valid, display just standard graph
            storage_totals = StorageCosts.objects.order_by().values('date__date__month').annotate(Live = Sum('unique_cost_live'), Archived=Sum('unique_cost_archived'))

            category_data_source = [{"name": "All projects", "data": list(storage_totals.values_list('Live',flat=True)), 'stack': 'Live'}, {"name": "All projects", "data": list(storage_totals.values_list('Archived',flat=True)), 'stack': 'Archived', 'linkedTo': ':previous'}]

            category_chart_data = {
                'chart': {'type': 'column', 'width': 1200,
            'height': 500, 'style': {
            'float': 'center'
                }},
                'title': {'text': 'Storage Costs'},
                'xAxis': {  	
                'categories': string_months},
                'yAxis': {'allowDecimals': 'false',
                    'min': '0',
                    'title': {
                        'text': 'Total cost'
                    },
                    'stackLabels': {
                        'enabled': 'true',
                        'allowOverlap':'true',
                        'style': {
                            'fontWeight': 'bold',
                            'color': 'gray',
                            'fontSize' : '12px'
                        }, 'format': "{stack}"
                    }}
                ,
                'setOptions': {
                    'lang': {
                        'thousandsSep': ','
                    }
                },
                'plotOptions': {'column': {'stacking': 'normal'}},
                'series': category_data_source
            }

            context = {
                'storage_data': json.dumps(category_chart_data),
                'form': form}
    
    else:
        # If nothing is submitted on the form (landing page)
        form = StorageForm()
        storage_totals = StorageCosts.objects.order_by().values('date__date__month').annotate(Live = Sum('unique_cost_live'), Archived=Sum('unique_cost_archived'))

        category_data_source = [{"name": "All projects", "data": list(storage_totals.values_list('Live',flat=True)), 'stack': 'Live'}, {"name": "All projects", "data": list(storage_totals.values_list('Archived',flat=True)), 'stack': 'Archived', 'linkedTo': ':previous'}]

        category_chart_data = {
                'chart': {'type': 'column', 'width': 1200,
            'height': 500, 'style': {
            'float': 'center'
        }},
                'title': {'text': 'Storage Costs'},
                'xAxis': {  	
                'categories': string_months},
                'yAxis': {'allowDecimals': 'false',
                    'min': '0',
                    'title': {
                        'text': 'Total cost'
                    },
                    'stackLabels': {
                        'enabled': 'true',
                        'allowOverlap':'true',
                        'style': {
                            'fontWeight': 'bold',
                            'color': 'gray',
                            'fontSize' : '12px'
                        }, 'format': "{stack}"
                    }}
                ,
                'setOptions': {
                    'lang': {
                        'thousandsSep': ','
                    }
                },
                'plotOptions': {'column': {'stacking': 'normal'}},
                'series': category_data_source
            }

        context = {
                'storage_data': json.dumps(category_chart_data),
                'form': form}

    return render(request, 'bar_chart.html', context)


    # live_proj_monthly = [StorageCosts.objects.filter(project__name__startswith=proj).values('date__date__month').annotate(sum = Sum('unique_cost_live')) for proj in proj_types]
    # live_proj_costs = [x[0].get('sum') for x in live_proj_monthly]
    # live_proj_months = [x[0].get('date__date__month') for x in live_proj_monthly]

    # archived_total_cost = StorageCosts.objects.values('date__date__month').annotate(total=Sum('unique_cost_archived'))
    # archived = archived_total_cost.values_list('total',flat=True)

    # fig = pgo.Figure()
    # fig.add_bar(x = proj_types, y = live_proj_prices, name = 'Live')
    # fig.add_bar(x = proj_types, y = archived_proj_prices, name = 'Archived')
    # fig.update_layout(title_text ="Storage cost per project type", yaxis_title = 'Total cost ($)', xaxis_title = 'Project type')

    # fig.add_bar(x = list_months, y = list_live, name = 'Live', hovertemplate = '<b>%{x}</b></br></br>' + 'Month: %{x}</br>' +'Total Cost: %{y}')
    # fig.add_bar(x = list_months, y = list_archived, name = 'Archived', hovertemplate = '<b>%{x}</b></br></br>' + 'Month: %{x}</br>' +'Total Cost: %{y}')
    # fig.update_layout(title_text ="Storage cost per month", yaxis_title = 'Total cost ($)', xaxis_title = 'Month')


    # chart = fig.to_html()
    # context = {'chart': chart}
    # return render(request, 'index.html', context)