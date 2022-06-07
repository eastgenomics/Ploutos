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
    # Get start and end from form
    totals = DailyOrgRunningTotal.objects.all()
    if 'submit' in request.GET:
        form = DateForm(request.GET)
        if form.is_valid():
            start = form.cleaned_data.get("start")
            end = form.cleaned_data.get("end")
            charge_type = form.cleaned_data.get("charge_type")

            # Filter totals based on the dates provided
            if start:
                totals = totals.filter(date__id__in = (
                    Dates.objects.filter(date__range=[start,end]
                    ).values_list('id',flat=True)))

                if charge_type == "Egress":
                    print("Charge type is egress")
                    y_data = [c.egress_charges for c in totals]
                elif charge_type == "Compute":
                    y_data = [c.compute_charges for c in totals]
                    print("Charge type is compute")
                elif charge_type == "Storage":
                    y_data = [c.storage_charges for c in totals]
                    print("Charge type is storage")

                fig = px.line(
                    x = [x.date.date for x in totals],
                    y = y_data,
                    title = "Running charges",
                    labels = {'x':'Date', 'y':'Charges ($)'}, width=1200, height=500
                )
                fig.update_layout(
                    title={
                        'font_size': 24,
                        'xanchor': 'center',
                        'x': 0.5
                })
        else:
            form = DateForm()

    else:
        form = DateForm()

    # Plot the date and storage charges as line graph

        compute = [c.compute_charges for c in totals]
        storage = [c.storage_charges for c in totals]
        egress = [c.egress_charges for c in totals]
        fig = px.line(
            x= [x.date.date for x in totals],
            y=compute,
            title = "Running charges total",
            labels = {'x':'Date', 'y':'Charges ($)'}, width=1200, height=500
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


def bar_chart(request):
    """Grouped bar chart by project type and month"""

    #assay_types = ['CEN', 'MYE', 'TWE', 'TSO500', 'SNP', 'CP', 'WES', 'PC']
    colours = ['#a6c96a','#c42525','#1aadce','#492970', '#003399', '#3366AA',
    '#f28f43', '#77a1e5', '#3D96AE', "#91e8e1"]

    # Find the months that exist in the db as categories 
    month_categories = list(StorageCosts.objects.order_by().values_list('date__date__month',flat=True).distinct())

    # Dict to convert integer month to named month
    date_conversion_dict = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}

    # Convert the months present in the db
    string_months = [x if x not in date_conversion_dict else date_conversion_dict[x] for x in month_categories]

    if 'submit' in request.GET:
        form = StorageForm(request.GET)
        if form.is_valid():
            print("Form is valid")
            proj_types = form.cleaned_data.get('project_type')

            if proj_types:
                count=-1
                category_data_source = []
                for proj_type in proj_types:
                    cost_list = StorageCosts.objects.filter(project__name__startswith= proj_type).order_by().values('date__date__month').annotate(Live = Sum('unique_cost_live'), Archived=Sum('unique_cost_archived'))
                    count+=1
                    live_data = {'name': proj_type, 'data': list(cost_list.values_list('Live',flat=True)), 'stack': 'Live', 'color': colours[count]}
                    category_data_source.append(live_data)
                    archived_data = {'name': proj_type, 'data': list(cost_list.values_list('Archived',flat=True)), 'stack': 'Archived', 'linkedTo': ':previous', 'color': colours[count]}
                    category_data_source.append(archived_data)
            elif form.cleaned_data.get('assay_type'):
                print("Assays selected")
        else:
            form = StorageForm()
            storage_totals = StorageCosts.objects.order_by().values('date__date__month').annotate(Live = Sum('unique_cost_live'), Archived=Sum('unique_cost_archived'))

            category_data_source = [{"name": "All projects", "data": list(storage_totals.values_list('Live',flat=True)), 'stack': 'Live'}, {"name": "all", "data": list(storage_totals.values_list('Archived',flat=True)), 'stack': 'Archived', 'linkedTo': ':previous'}]
    
    else:
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