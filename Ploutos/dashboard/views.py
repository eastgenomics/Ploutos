"""Views containing logic for chart plotting"""
import calendar
import json
import pandas as pd

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from dashboard.forms import (
    DateForm, MonthlyForm, StorageForm, FileForm
)
from dashboard.models import DailyOrgRunningTotal
from django.shortcuts import render
from scripts import DNAnexus_queries as dx_queries
from scripts import file_plots as fp
from scripts.running_total_plots import RunningTotPlotFunctions
from scripts import storage_plots as sp

rtp = RunningTotPlotFunctions()


def index(request):
    """View to display running total charges via Plotly"""
    # Get all running total objects from db
    # Get first date of month four months ago + first date of next month
    # To be used for all default filtering
    totals = DailyOrgRunningTotal.objects.all()
    four_months_ago = date.today() + relativedelta(months=-4)
    start_of_four_months_ago = four_months_ago.replace(day=1)
    start_of_next_month = (
        date.today() + relativedelta(months=+1)
    ).replace(day=1)

    # If the form is submitted
    if 'submit' in request.GET:
        # Get the form with info, set monthly form and monthly plot to default
        form = DateForm(request.GET)
        form2 = MonthlyForm()
        monthly_chart, monthly_df = rtp.monthly_between_dates(
            start_of_four_months_ago, start_of_next_month
        )

        # If the dates entered are validated
        if form.is_valid():

            # If there's a date entered get dates
            if form.cleaned_data.get("start"):
                start = form.cleaned_data.get("start")
                end = form.cleaned_data.get("end")
                # Add one day to the end as total for a day
                # Is relative to the next day minus that day
                end_obj = datetime.strptime(str(end), "%Y-%m-%d")
                end_plus_one = end_obj + timedelta(days=1)
                end_plus_one_str = datetime.strftime(
                    end_plus_one, "%Y-%m-%d"
                )

                # Filter totals to get desired date range
                totals = totals.filter(
                    date__date__range=[start, end_plus_one_str]
                )

                # If user wants to see all charge types, render whole graph
                # if charge_type == 'All':
                fig, daily_df = rtp.daily_plot(totals)
                daily_chart = fig.to_html()

                # Filtered daily_chart and default monthly_chart to context
                # Send validated form and empty form2 to context
                context = {
                    'daily_chart': daily_chart,
                    'monthly_chart': monthly_chart,
                    'form': form,
                    'form2': form2,
                    'monthly_df': monthly_df,
                    'daily_df': daily_df
                }

            else:
                # No dates are entered so show default last 4 months
                totals = totals.filter(
                    date__date__range=[
                        start_of_four_months_ago, date.today()
                    ]
                )

                fig, daily_df = rtp.daily_plot(totals)
                daily_chart = fig.to_html()

                context = {
                    'daily_chart': daily_chart,
                    'monthly_chart': monthly_chart,
                    'form': form,
                    'form2': form2,
                    'monthly_df': monthly_df,
                    'daily_df': daily_df
                }

        else:
            # If form not valid or unsubmitted
            # Display unfiltered graph for all dates and show errors
            totals = totals.filter(
                date__date__range=[
                    start_of_four_months_ago, date.today()
                ]
            )

            fig, daily_df = rtp.daily_plot(totals)
            daily_chart = fig.to_html()

            context = {
                'daily_chart': daily_chart,
                'monthly_chart': monthly_chart,
                'form': form,
                'form2': form2,
                'monthly_df': monthly_df,
                'daily_df': daily_df
            }

    # If instead form for monthly chart is submitted
    elif 'monthly' in request.GET:
        totals = totals.filter(
            date__date__range=[
                start_of_four_months_ago, date.today()
            ]
        )
        form = DateForm()
        form2 = MonthlyForm(request.GET)

        if form2.is_valid():
            start_month = form2.cleaned_data.get("start_month")
            end_month = form2.cleaned_data.get("end_month")

            # If no months entered
            if start_month == "---" and end_month == "---":

                # Display last four months on monthly plot
                monthly_chart, monthly_df = rtp.monthly_between_dates(
                    start_of_four_months_ago, start_of_next_month
                )
                # And last four months on daily plot
                fig, daily_df = rtp.daily_plot(totals)
                daily_chart = fig.to_html()

                context = {
                    'daily_chart': daily_chart,
                    'monthly_chart': monthly_chart,
                    'form': form,
                    'form2': form2,
                    'monthly_df': monthly_df,
                    'daily_df': daily_df
                }

            else:
                # If months are entered
                month_start = f"{start_month}-01"
                month_end = f"{end_month}-01"
                # Convert to date obj
                date_month_end = datetime.strptime(
                    month_end, "%Y-%m-%d"
                ).date()
                # Add one month to the end month
                # So it is first of next month
                month_end = date_month_end + relativedelta(months=+1)
                monthly_chart, monthly_df = rtp.monthly_between_dates(
                    month_start, month_end
                )
                # Show last four months on daily plot
                fig, daily_df = rtp.daily_plot(totals)
                daily_chart = fig.to_html()

                context = {
                    'daily_chart': daily_chart,
                    'monthly_chart': monthly_chart,
                    'form': form,
                    'form2': form2,
                    'monthly_df': monthly_df,
                    'daily_df': daily_df
                }

        else:
            # If monthly form not valid or unsubmitted
            # Display unfiltered graph for all dates and show errors
            monthly_chart, monthly_df = rtp.monthly_between_dates(
                start_of_four_months_ago, start_of_next_month
            )
            # Show last four months on daily plot
            fig, daily_df = rtp.daily_plot(totals)
            daily_chart = fig.to_html()

            context = {
                'daily_chart': daily_chart,
                'monthly_chart': monthly_chart,
                'form': form,
                'form2': form2,
                'monthly_df': monthly_df,
                'daily_df': daily_df
            }

    # If no forms submitted display last four months for daily + monthly
    else:
        form = DateForm()
        form2 = MonthlyForm()
        monthly_chart, monthly_df = rtp.monthly_between_dates(
            start_of_four_months_ago, start_of_next_month
        )

        fig, daily_df = rtp.daily_plot(totals)
        daily_chart = fig.to_html()

        context = {
            'daily_chart': daily_chart,
            'monthly_chart': monthly_chart,
            'form': form,
            'form2': form2,
            'monthly_df': monthly_df,
            'daily_df': daily_df
        }

    return render(request, 'index.html', context)


def storage_chart(request):
    """
    Creates a bar chart grouped by month with each month having two bars
    Denoting live vs archived status
    Each bar is stacked with either project type
    Or assay type depending on the filters entered
    """
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
    # If the user has submitted the form
    if 'submit' in request.GET:
        form = StorageForm(request.GET)
        # If form is valid
        # i.e. not >1 entry in project_types and assay_types at same time
        if form.is_valid():
            # Get the start + end year-months from form to filter range
            start = form.cleaned_data.get("start")
            end = form.cleaned_data.get("end")

            # If no months are entered
            if start == "---" and end == "---":

                # If no months entered but proj type and assay type searched
                if (form.cleaned_data.get('project_type') and
                    form.cleaned_data.get('assay_type')):
                    project_type = form.cleaned_data.get('project_type')
                    assay_type = form.cleaned_data.get('assay_type')

                    # Month ranges are last four months
                    context = sp.StoragePlotFunctions(
                    ).month_range_assay_type_and_proj_type(
                        project_type,
                        assay_type,
                        four_months_start,
                        this_months_end,
                        form
                    )

                # No months entered
                # There are either project types or assay types searched
                else:
                    # If there are only projects searched for
                    if form.cleaned_data.get('project_type'):
                        # Remove all whitespace + start + end commas
                        # Split by commas and add each to new list
                        proj_string = form.cleaned_data.get('project_type')
                        proj_types = sp.StoragePlotFunctions(
                        ).str_to_list(proj_string)

                        # Month ranges are last four months
                        context = sp.StoragePlotFunctions(
                        ).month_range_only_project_types(
                            proj_types,
                            four_months_start,
                            this_months_end,
                            form
                        )

                    # If only assay(s) searched for
                    # Strip start and end commas, remove whitespace
                    # Split on commas and add to list
                    elif form.cleaned_data.get('assay_type'):
                        assay_string = form.cleaned_data.get('assay_type')
                        assay_types = sp.StoragePlotFunctions(
                        ).str_to_list(assay_string)

                        # Month ranges are last four months
                        context = sp.StoragePlotFunctions(
                        ).month_range_only_assay_types(
                            assay_types,
                            four_months_start,
                            this_months_end,
                            form
                        )

                    else:
                        # If form is submitted
                        # But no assay type or project type is searched for
                        # And no months searched for
                        # Display all projs last 4 months grouped by month

                        context = sp.StoragePlotFunctions(
                            ).all_projects_between_months(
                                four_months_start,
                                this_months_end,
                                form
                            )

            else:
                # Start and end months are entered
                # Convert start month-year to 1st date of start month
                # e.g. "2022-05" to "2022-05-01"
                # Find last day of the end month
                # Convert end month-year to last day of that month
                # e.g. "2022-05-14" to "2022-05-31"
                month_start = f"{start}-01"
                last_day_of_end_month = calendar.monthrange(
                    int(end.split("-")[0]), int(end.split("-")[1])
                )[1]
                month_end = f"{end}-{last_day_of_end_month}"

                # If there are both a project type and assay type entered
                # Get the single string from each
                if (form.cleaned_data.get('project_type') and
                    form.cleaned_data.get('assay_type')):
                    project_type = form.cleaned_data.get(
                        'project_type'
                    ).strip()
                    assay_type = form.cleaned_data.get('assay_type').strip()

                    # Filter by start date of start month-year
                    # And end date of end month-year
                    context = sp.StoragePlotFunctions(
                    ).month_range_assay_type_and_proj_type(
                        project_type,
                        assay_type,
                        month_start,
                        month_end,
                        form
                    )

                else:
                    # There are only projects searched for
                    if form.cleaned_data.get('project_type'):
                        # Remove all whitespace + start + end commas
                        # Split by commas and add each to new list
                        proj_string = form.cleaned_data.get('project_type')
                        proj_types = sp.StoragePlotFunctions(
                        ).str_to_list(proj_string)

                        # Filter by start date of start month-year
                        # And end date of end month-year
                        context = sp.StoragePlotFunctions(
                        ).month_range_only_project_types(
                            proj_types,
                            month_start,
                            month_end,
                            form
                        )

                    # If only assay(s) searched for
                    # Strip start and end commas, remove whitespace
                    # Split on commas and add to list
                    elif form.cleaned_data.get('assay_type'):
                        assay_string = form.cleaned_data.get('assay_type')
                        assay_types = sp.StoragePlotFunctions(
                        ).str_to_list(assay_string)

                        # Filter by start date of start month-year
                        # And end date of end month-year
                        context = sp.StoragePlotFunctions(
                        ).month_range_only_assay_types(
                            assay_types,
                            month_start,
                            month_end,
                            form
                        )

                    else:
                        # If form is submitted
                        # But no assay type or project type is searched for
                        # And want to see between month range
                        # Display all the projects grouped by months

                        context = sp.StoragePlotFunctions(
                        ).all_projects_between_months(
                            month_start,
                            month_end,
                            form
                        )

        else:
            # If the form is not valid, display just the standard graph
            # Grouped by last four months
            # For all projects
            context = sp.StoragePlotFunctions(
                ).all_projects_between_months(
                    four_months_start,
                    this_months_end,
                    form
                )

    elif 'clear' in request.GET:
        form = StorageForm()
        context = sp.StoragePlotFunctions(
        ).all_projects_between_months(
            four_months_start,
            this_months_end,
            form
        )

    else:
        # If nothing is submitted on the form (normal landing page)
        # Display the all projects graph grouped by last four months
        form = StorageForm()
        context = sp.StoragePlotFunctions(
            ).all_projects_between_months(
                four_months_start,
                this_months_end,
                form
            )

    return render(request, 'bar_chart.html', context)


def files(request):
    """View for displaying the file type data"""
    date_to_filter = date.today()
    live_total, archived_total = sp.StoragePlotFunctions(
    ).get_todays_total_unique_size()
    proj_level_df = pd.DataFrame()

    # If the user has submitted the form
    if 'submit' in request.GET:
        form = FileForm(request.GET)
        # If form is valid
        # i.e. not >1 entry in project_types and assay_types at same time
        if form.is_valid():
            if form.cleaned_data.get('date_to_filter'):
                date_to_filter = form.cleaned_data.get('date_to_filter')
            else:
                date_to_filter = date.today()

            # If a project type and assay type is entered
            # Plot sizes + counts for the combination
            if (form.cleaned_data.get('project_type') and
                form.cleaned_data.get('assay_type')):
                project_type = form.cleaned_data.get('project_type').strip()
                assay_type = form.cleaned_data.get('assay_type').strip()

                count_chart_data, count_df = fp.FilePlotFunctions(
                ).file_types_count_assay_and_proj_types(
                    date_to_filter, project_type, assay_type
                )

                size_chart_data, size_df, proj_level_df = fp.FilePlotFunctions(
                ).file_types_size_assay_and_proj_types(
                    date_to_filter, project_type, assay_type
                )

            else:
                # If just project types entered
                # Plot sizes + counts for those proj types
                if form.cleaned_data.get('project_type'):
                    proj_string = form.cleaned_data.get('project_type')
                    proj_types = sp.StoragePlotFunctions(
                    ).str_to_list(proj_string)

                    count_chart_data, count_df = fp.FilePlotFunctions(
                    ).file_types_count_project_types(
                        date_to_filter, proj_types
                    )

                    size_chart_data, size_df, proj_level_df = (
                        fp.FilePlotFunctions().file_types_size_project_types(
                            date_to_filter, proj_types
                        )
                    )

                # If just assay types are entered
                # Plot sizes + counts for those assay types
                elif form.cleaned_data.get('assay_type'):
                    assay_string = form.cleaned_data.get('assay_type')
                    assay_types = sp.StoragePlotFunctions(
                    ).str_to_list(assay_string)

                    count_chart_data, count_df = fp.FilePlotFunctions(
                    ).file_types_count_assay_types(
                        date_to_filter, assay_types
                    )

                    size_chart_data, size_df, proj_level_df = (
                        fp.FilePlotFunctions().file_types_size_assay_types(
                            date_to_filter, assay_types
                        )
                    )

                else:
                    # If form submitted but no projects or assays searched for
                    # Show today's sizes + counts
                    size_chart_data, size_df, proj_level_df = (
                        fp.FilePlotFunctions().file_types_size_all_projects(
                            date_to_filter
                        )
                    )

                    count_chart_data, count_df = fp.FilePlotFunctions(
                    ).file_types_count_all_projects(date_to_filter)

        else:
            # Form is not valid
            # Go back to showing today's sizes + counts
            size_chart_data, size_df, proj_level_df = fp.FilePlotFunctions(
            ).file_types_size_all_projects(date_to_filter)

            count_chart_data, count_df = fp.FilePlotFunctions(
            ).file_types_count_all_projects(date_to_filter)

    elif 'clear' in request.GET:
        form = FileForm()
        size_chart_data, size_df, proj_level_df = fp.FilePlotFunctions(
        ).file_types_size_all_projects(date_to_filter)

        count_chart_data, count_df = fp.FilePlotFunctions(
        ).file_types_count_all_projects(date_to_filter)

    else:
        # Nothing is submitted
        # Show today's sizes + counts
        form = FileForm()

        size_chart_data, size_df, proj_level_df = fp.FilePlotFunctions(
        ).file_types_size_all_projects(date_to_filter)

        count_chart_data, count_df = fp.FilePlotFunctions(
            ).file_types_count_all_projects(date_to_filter)

    context = {
        'live_total': live_total,
        'archived_total': archived_total,
        'file_size_data': json.dumps(size_chart_data),
        'size_df': size_df,
        'file_count_data': json.dumps(count_chart_data),
        'count_df': count_df,
        'form1': form,
        'detailed_df': proj_level_df,
        'date_to_display': date_to_filter
    }

    return render(request, 'files.html', context)

def jobs(request):
    """View to display the jobs data"""
    return render(request, 'jobs.html')
