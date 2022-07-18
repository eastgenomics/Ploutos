import datetime
import calendar
import json
import plotly.express as px
import plotly.graph_objects as pgo

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from dashboard.forms import DateForm, StorageForm, ComputeForm
from dashboard.models import ComputeCosts, Dates, DailyOrgRunningTotal
from django.db.models import Sum
from django.shortcuts import render
from scripts import DNAnexus_queries as dx_queries
from scripts import storage_plots as sp
from scripts import executions_plots as exec_plots
from scripts import date_conversion as dc


def index(request):
    """View to display running total charges via Plotly"""
    # Get all running total objects from db
    totals = DailyOrgRunningTotal.objects.all()

    # If the form is submitted
    if 'submit' in request.GET:
        form = DateForm(request.GET)
        # If the dates entered are validated ok
        if form.is_valid():
            # Get the data entered
            start = form.cleaned_data.get("start")
            end = form.cleaned_data.get("end")
            charge_type = form.cleaned_data.get("charge_type")

            # Filter totals to get desired date range
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
                fig = sp.RunningTotPlotFunctions().all_charge_types(totals)

            # If a specific charge type chosen, set y_data accordingly
            else:
                fig = sp.RunningTotPlotFunctions().specific_charge_type(
                    totals,
                    charge_type
                )

            # Update layout
            fig.update_layout(
                title={
                    'font_size': 24,
                    'xanchor': 'center',
                    'x': 0.5
                }
            )

            # Send to context
            chart = fig.to_html()
            context = {'chart': chart, 'form': form}

        else:
            # If form not valid
            # Display unfiltered graph for all dates and show errors
            context = sp.RunningTotPlotFunctions().totals_form_not_valid(
                totals,
                form
            )

    else:
        # If form not submitted display all charges for all dates in db
        form = DateForm()

        context = sp.RunningTotPlotFunctions().form_not_submitted(
            totals,
            form
        )

    return render(request, 'index.html', context)


def storage_chart(request):
    """
    Creates a bar chart grouped by month with each month having two bars
    Denoting live vs archived status
    Each bar is stacked with either project type
    Or assay type depending on the filters entered
    """

    # If the user has submitted the form
    if 'submit' in request.GET:
        form = StorageForm(request.GET)
        # If form is valid
        # i.e. not >1 entry in project_types and assay_types at same time
        if form.is_valid():
            year = form.cleaned_data.get('year')
            month = form.cleaned_data.get('month')

            # If user wants to see all the months in the db
            if month == 'All':
                # If there are both a project type and assay type entered
                # Get the single string from each
                if (form.cleaned_data.get('project_type') and
                        form.cleaned_data.get('assay_type')):
                    project_type = form.cleaned_data.get('project_type')
                    assay_type = form.cleaned_data.get('assay_type')

                    context = sp.StoragePlotFunctions(
                    ).all_months_assay_type_and_proj_type(
                        project_type,
                        assay_type,
                        year,
                        form
                    )

                else:
                    # If 'All' months selected and
                    # There are only projects searched for
                    if form.cleaned_data.get('project_type'):
                        # Remove all whitespace + start + end commas
                        # Split by commas and add each to new list
                        proj_string = form.cleaned_data.get('project_type')
                        proj_types = sp.StoragePlotFunctions(
                        ).str_to_list(proj_string)

                        context = sp.StoragePlotFunctions(
                        ).all_months_only_project_types(
                            proj_types,
                            year,
                            form
                        )

                    # If all months only assay(s) searched for
                    # Strip start and end commas, remove whitespace
                    # Split on commas and add to list
                    elif form.cleaned_data.get('assay_type'):
                        assay_string = form.cleaned_data.get('assay_type')
                        assay_types = sp.StoragePlotFunctions(
                        ).str_to_list(assay_string)

                        context = sp.StoragePlotFunctions(
                        ).all_months_only_assay_types(
                            assay_types,
                            year,
                            form
                        )

                    else:
                        # If form is submitted
                        # But no assay type or project type is searched for
                        # And want to see all months
                        # Display all the projects grouped by available months

                        context = sp.StoragePlotFunctions(
                        ).all_months_form_submitted_no_proj_or_assay(
                            year,
                            form
                        )

            # A specific month has been selected
            else:
                # Convert the integer month to a string
                converted_month = dc.date_conversion_dict[int(month)]

                # If a project type and an assay type entered
                if (form.cleaned_data.get('project_type') and
                        form.cleaned_data.get('assay_type')):
                    project_type = form.cleaned_data.get('project_type')
                    assay_type = form.cleaned_data.get('assay_type')

                    context = sp.StoragePlotFunctions(
                    ).specific_month_proj_and_assay(
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
                    proj_types = sp.StoragePlotFunctions(
                    ).str_to_list(proj_string)

                    context = sp.StoragePlotFunctions(
                    ).specific_month_only_proj_types(
                        proj_types,
                        year,
                        month,
                        converted_month,
                        form
                    )

                # A specific month with assay type(s)
                elif form.cleaned_data.get('assay_type'):
                    assay_string = form.cleaned_data.get('assay_type')
                    assay_types = sp.StoragePlotFunctions(
                    ).str_to_list(assay_string)

                    context = sp.StoragePlotFunctions(
                    ).specific_month_only_assay_types(
                        assay_types,
                        year,
                        month,
                        converted_month,
                        form
                    )

                else:
                    # If form submitted + no proj or assay type
                    # But specific year/month selected (required fields)
                    context = sp.StoragePlotFunctions(
                    ).specific_month_no_proj_or_assay(
                        year,
                        month,
                        converted_month,
                        form
                    )

        else:
            # If the form is not valid, display just the standard graph
            # Of this year, grouped by available months
            # For all projects
            context = sp.StoragePlotFunctions().form_is_not_submitted_or_invalid(form)

    else:
        # If nothing is submitted on the form (normal landing page)
        # Display the all projects graph grouped by available months
        form = StorageForm()
        context = sp.StoragePlotFunctions().form_is_not_submitted_or_invalid(
            form
        )

    return render(request, 'bar_chart.html', context)


def compute_graph(request):
    """
    Creates a bar chart grouped by month with each month having two bars
    Each bar is stacked with either project type
    Or assay type depending on the filters entered.
    """
    context = {
        'compute_data': "",
        'form': ""
    }

    # If the user has submitted the form
    if 'Daily' in request.GET:
        # submit = Daily graphs.
        form = ComputeForm(request.GET)
        # If form is valid
        if form.is_valid():
            year = form.cleaned_data.get('year')
            month = form.cleaned_data.get('month')
            # Get the start + end year-months from form to filter range
            start = form.cleaned_data.get("start")
            end = form.cleaned_data.get("end")
            if start == "---" and end == "---":
                # Get date of the first day of the month four months ago
                # Get date of the last day of the current month
                # These are used to filter for last 4 months by default
                today_date = dx_queries.no_of_days_in_month()[0]
                this_year, this_month, _ = today_date.split("-")
                four_months_ago = date.today() + relativedelta(months=-4)
                four_months_start = four_months_ago.replace(day=1)
                last_day_of_this_month = str(
                    calendar.monthrange(
                        int(today_date.split("-")[0]),
                        int(today_date.split("-")[1])
                    )[1]
                )
                this_months_end = (
                    f"{this_year}-{this_month}"
                    f"-{last_day_of_this_month}"
                )
                # If there are both a project type and assay type entered
                # Get the single string from each
                if (form.cleaned_data.get('project_type') and
                        form.cleaned_data.get('assay_type')):
                    project_types = form.cleaned_data.get('project_type')
                    assay_types = form.cleaned_data.get('assay_type')

                    json_chart_data, chart_df = exec_plots.ExecutionPlotFunctions(
                    ).daily_last_4_months_all_byproject_and_assay(
                        project_types,
                        assay_types,
                        form
                    )
                    context = {
                        "compute_data": json_chart_data,
                        "form": form,
                        "chart_df": chart_df
                    }

                    return render(request, 'daily_compute_graph.html', context)

                # If there is a project type entered
                # Get the single string from each
                elif form.cleaned_data.get('project_type'):
                    project_types = form.cleaned_data.get('project_type')
                    json_chart_data, chart_df = exec_plots.ExecutionPlotFunctions(
                    ).daily_last_4_months_all_byproject_types(
                        project_types,
                        form
                    )
                    context = {
                        "compute_data": json_chart_data,
                        "form": form,
                        "chart_df": chart_df
                    }
                    print("testing")

                    return render(request, 'daily_compute_graph.html', context)

                # If there is an assay type entered
                # Get the single string from each
                elif form.cleaned_data.get('assay_type'):
                    assay_types = form.cleaned_data.get('assay_type')
                    json_chart_data, chart_df = exec_plots.ExecutionPlotFunctions(
                    ).daily_last_4_months_all_byassay_types(
                        assay_types,
                        form
                    )
                    context = {
                        "compute_data": json_chart_data,
                        "form": form,
                        "chart_df": chart_df
                    }

                    return render(request, 'daily_compute_graph.html', context)

                else:
                    context = exec_plots.ExecutionPlotFunctions(
                    ).default_daily_all_project(
                        form
                    )

                    return render(request, 'daily_compute_graph.html', context)

            else:
                # If no time period selected and
                # There are only projects searched for
                if form.cleaned_data.get('project_type'):
                    # Remove all whitespace + start + end commas
                    # Split by commas and add each to new list
                    proj_string = form.cleaned_data.get('project_type')
                    proj_types = exec_plots.ExecutionPlotFunctions(
                    ).str_to_list(proj_string)
                    context = exec_plots.ExecutionPlotFunctions(
                    ).all_months_only_project_types(
                        proj_types,
                        form
                    )
                    return render(request, 'daily_compute_graph.html', context)

                # If all months only assay(s) searched for
                # Strip start and end commas, remove whitespace
                # Split on commas and add to list
                elif form.cleaned_data.get('assay_type'):
                    assay_string = form.cleaned_data.get('assay_type')
                    assay_types = exec_plots.ExecutionPlotFunctions(
                    ).str_to_list(assay_string)
                    context = exec_plots.ExecutionPlotFunctions(
                    ).all_months_only_assay_types(
                        assay_types,
                        year,
                        form
                    )
                    return render(request, 'daily_compute_graph.html', context)
                else:
                    # If form is submitted
                    # But no assay type or project type is searched for
                    # And want to see default months
                    context = exec_plots.ExecutionPlotFunctions(
                    ).daily_last_4_months_all_project_types(
                        proj_types,
                        form
                    )

                    return render(request, 'daily_compute_graph.html', context)

        else:
            # If nothing is submitted on the form (normal landing page)
            # Display the all projects graph grouped by available months
            form = ComputeForm()
            # print(ComputeForm.errors)
            context = exec_plots.ExecutionPlotFunctions().default_daily_all_project(
                form
            )

            return render(request, 'daily_compute_graph.html', context)

    elif 'Monthly' in request.GET:
        form = ComputeForm(request.GET)
        if form.is_valid():
            year = form.cleaned_data.get('year')
            month = form.cleaned_data.get('month')
            # Get the start + end year-months from form to filter range
            # start = form.cleaned_data.get("start")
            # end = form.cleaned_data.get("end")
            # if start == "---" and end == "---":
            #     # Get date of the first day of the month four months ago
            #     # Get date of the last day of the current month
            #     # These are used to filter for last 4 months by default
            #     today_date = dx_queries.no_of_days_in_month()[0]
            #     this_year, this_month, _ = today_date.split("-")
            #     four_months_ago = date.today() + relativedelta(months=-4)
            #     four_months_start = four_months_ago.replace(day=1)
            #     last_day_of_this_month = str(
            #         calendar.monthrange(
            #             int(today_date.split("-")[0]),
            #             int(today_date.split("-")[1])
            #         )[1]
            #     )
            #     this_months_end = (
            #         f"{this_year}-{this_month}"
            #         f"-{last_day_of_this_month}"
            #     )

            # If there are both a project type and assay type entered
            # Get the single string from each
            if (form.cleaned_data.get('project_type') and
                    form.cleaned_data.get('assay_type')):
                print("YES")
                print(form.cleaned_data.get('project_type'))
                project_types = form.cleaned_data.get('project_type')
                assay_types = form.cleaned_data.get('assay_type')
                json_chart_data, chart_df = exec_plots.ExecutionPlotFunctions().monthly_byproject_assays_stacked(
                    project_types,
                    assay_types,
                    form
                )
                context = {
                    "compute_data": json_chart_data,
                    "form": form,
                    "chart_df": chart_df
                }

                return render(request, 'monthly_compute_graph.html', context)

            elif form.cleaned_data.get('project_type'):
                project_types = form.cleaned_data.get('project_type')
                json_chart_data, chart_df = exec_plots.ExecutionPlotFunctions(
                ).monthly_byproject(
                    project_types,
                    form
                )
                context = {
                    "compute_data": json_chart_data,
                    "form": form,
                    "chart_df": chart_df
                }

                return render(request, 'monthly_compute_graph.html', context)

            elif form.cleaned_data.get('assay_type'):
                assay_types = form.cleaned_data.get('assay_type')
                json_chart_data, chart_df = exec_plots.ExecutionPlotFunctions(
                ).monthly_byassay(
                    assay_types,
                    form
                )
                context = {
                    "compute_data": json_chart_data,
                    "form": form,
                    "chart_df": chart_df
                }

                return render(request, 'monthly_compute_graph.html', context)

            else:
                # months selected but display default currently.
                form = ComputeForm()
                json_chart_data, chart_df = exec_plots.ExecutionPlotFunctions().All_projects_by_months(form)
                context = {
                    "compute_data": json_chart_data,
                    "form": form,
                    "chart_df": chart_df
                }

                return render(request, 'monthly_compute_graph.html', context)

        else:
            # Display default months_filtered graph
            form = ComputeForm()
            json_chart_data, chart_df = exec_plots.ExecutionPlotFunctions(
            ).All_projects_by_months(
                form
            )
            context = {
                "compute_data": json_chart_data,
                "form": form,
                "chart_df": chart_df
            }

            return render(request, 'monthly_compute_graph.html', context)
    else:
        # If nothing is submitted on the form (normal landing page)
        # Display the all projects graph grouped by daily results.
        form = ComputeForm()
        context = exec_plots.ExecutionPlotFunctions().default_daily_all_project(
            form
        )
        return render(request, 'daily_compute_graph.html', context)


# def leaderboard(request):
#     context = {
#         'compute_data': "",
#         'form': ""
#     }

#     # If the user has submitted the form
#     if 'Daily' in request.GET:
#         if (form.cleaned_data.get('project_type') and
#                 form.cleaned_data.get('assay_type')):
#             project_types = form.cleaned_data.get('project_type')
#             assay_types = form.cleaned_data.get('assay_type')
#             json_chart_data, chart_df = exec_plots.ExecutionPlotFunctions(
#             ).daily_last_4_months_all_byproject_and_assay(
#                 project_types,
#                 assay_types,
#                 form
#             )
#             context = {
#                 "compute_data": json_chart_data,
#                 "form": form,
#                 "chart_df": chart_df

#             return render(request, 'daily_compute_graph.html', context
#         # If there is a project type entered
#         # Get the single string from each
#         elif form.cleaned_data.get('project_type'):
#             project_types = form.cleaned_data.get('project_type')
#             json_chart_data, chart_df = exec_plots.ExecutionPlotFunctions(
#             ).daily_last_4_months_all_byproject_types(
#                 project_types,
#                 form
#             )
#             context = {
#                 "compute_data": json_chart_data,
#                 "form": form,
#                 "chart_df": chart_df
#             }
#             print("testing"
#             return render(request, 'daily_compute_graph.html', context
#         # If there is an assay type entered
#         # Get the single string from each
#         elif form.cleaned_data.get('assay_type'):
#             assay_types = form.cleaned_data.get('assay_type')
#             json_chart_data, chart_df = exec_plots.ExecutionPlotFunctions(
#             ).daily_last_4_months_all_byassay_types(
#                 assay_types,
#                 form
#             )
#             context = {
#                 "compute_data": json_chart_data,
#                 "form": form,
#                 "chart_df": chart_df

#             return render(request, 'daily_compute_graph.html', context
#         else:
#             context = exec_plots.ExecutionPlotFunctions(
#             ).default_daily_all_project(
#                 form

#             return render(request, 'daily_compute_graph.html', context)
#     elif 'Monthly' in request.GET:
        
        
#     else:
#         print("Invalid")

#     return render(request, 'leaderboard.html', context)


