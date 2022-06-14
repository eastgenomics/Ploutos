import datetime
import json
import plotly.express as px
import plotly.graph_objects as pgo

from dashboard.forms import DateForm, StorageForm
from dashboard.models import (
    Users, Projects, Dates, DailyOrgRunningTotal, StorageCosts
)
from django.db.models import Sum
from django.shortcuts import render
from scripts import DNAnexus_queries as q
from scripts import storage_plots as sp


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
                    date__id__in=(
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

                    context = sp.StoragePlotFunctions().all_months_assay_type_and_proj_type(
                        project_type,
                        assay_type,
                        year,
                        string_months,
                        form
                    )
                
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
                        
                        context = sp.StoragePlotFunctions().all_months_only_project_types(
                            proj_types,
                            year,
                            string_months,
                            form
                        )

                    # If all months only assay(s) searched for
                    # Strip start and end commas, remove whitespace
                    # Split on commas and add to list
                    elif form.cleaned_data.get('assay_type'):
                        assay_string = form.cleaned_data.get('assay_type')
                        assay_types = assay_string.strip(",").replace(
                            " ", ""
                            ).split(",")

                        context = sp.StoragePlotFunctions().all_months_only_assay_types(
                            assay_types,
                            year,
                            string_months,
                            form
                        )
                    
                    else:
                        # If form is submitted
                        # But no assay type or project type is searched for
                        # And want to see all months
                        # Display all the projects grouped by available months

                        context = sp.StoragePlotFunctions().all_months_form_submitted_no_proj_or_assay(
                            year,
                            string_months,
                            form
                        )

            # A specific month has been selected
            else:
                # Convert the integer month to a string
                converted_month = date_conversion_dict[int(month)]

                # If a project type and an assay type entered
                if (form.cleaned_data.get('project_type') and
                form.cleaned_data.get('assay_type')):
                    project_type = form.cleaned_data.get('project_type')
                    assay_type = form.cleaned_data.get('assay_type')

                    context = sp.StoragePlotFunctions().specific_month_proj_and_assay(
                        project_type,
                        assay_type,
                        year,
                        month,
                        converted_month,
                        form
                    )

                # A specific month with only project type(s)
                elif form.cleaned_data.get('project_type'):
                    proj_string = form.cleaned_data.get('project_type')
                    # Strip commas from start and end
                    # Remove whitespace, split into list on commas
                    proj_types = proj_string.strip(",").replace(
                        " ", ""
                        ).split(",")
                    
                    context = sp.StoragePlotFunctions().specific_month_only_proj_types(
                        proj_types,
                        year,
                        month,
                        converted_month,
                        form
                    )

                # A specific month with assay type(s)
                elif form.cleaned_data.get('assay_type'):
                    assay_string = form.cleaned_data.get('assay_type')
                    assay_types = assay_string.strip(",").replace(
                        " ", ""
                        ).split(",")

                    context = sp.StoragePlotFunctions().specific_month_only_assay_types(
                        assay_types,
                        year,
                        month,
                        converted_month,
                        form
                    )
                
                else:
                    # If form submitted
                    # But no proj or assay type but specific year/month selected
                    # Because those fields are required
                    context = sp.StoragePlotFunctions().specific_month_no_proj_or_assay(
                        year,
                        month,
                        converted_month,
                        form
                    )

        else:
            # If the form is not valid, display just the standard graph
            # Of this year, grouped by available months
            # For all projects
            context = sp.StoragePlotFunctions().form_is_not_valid(
                string_months,
                form
            )
    
    else:
        # If nothing is submitted on the form (normal landing page)
        # Display the all projects graph grouped by available months
        form = StorageForm()
        context = sp.StoragePlotFunctions().form_is_not_submitted(
            string_months,
            form
        )

    return render(request, 'bar_chart.html', context)

def jobs(request):
    """View to display the jobs data"""
    return render(request, 'jobs.html')
