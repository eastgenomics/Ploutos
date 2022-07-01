"""Views containing logic for chart plotting"""
import calendar

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from dashboard.forms import DateForm, MonthlyForm, StorageForm
from dashboard.models import DailyOrgRunningTotal
from django.shortcuts import render
from scripts import DNAnexus_queries as dx_queries
from scripts import storage_plots as sp


def index(request):
    """View to display running total charges via Plotly"""
    # Get all running total objects from db
    totals = DailyOrgRunningTotal.objects.all()
    four_months_ago = date.today() + relativedelta(months=-4)
    start_of_four_months_ago = four_months_ago.replace(day=1)
    start_of_next_month = (
        date.today() + relativedelta(months=+1)
    ).replace(day=1)
    # If the form is submitted
    if 'submit' in request.GET:
        # Get the form, set monthly form and monthly plot to default
        form = DateForm(request.GET)
        form2 = MonthlyForm()
        chart2 = sp.RunningTotPlotFunctions().monthly_between_dates(
            start_of_four_months_ago, start_of_next_month
        )

        # If the dates entered are validated ok
        if form.is_valid():
            # Get the charge type (always entered)
            charge_type = form.cleaned_data.get("charge_type")

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
                totals = DailyOrgRunningTotal.objects.filter(
                    date__date__range=[start, end_plus_one_str]
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

                chart = fig.to_html()

                # Send filtered chart1 and unfiltered chart 2 to context
                # Send validated form and empty form2 to context
                context = {
                    'chart': chart,
                    'chart2': chart2,
                    'form': form,
                    'form2': form2
                }

            else:
                # No dates are entered so show default last 4 months
                totals = DailyOrgRunningTotal.objects.filter(
                    date__date__range=[start_of_four_months_ago, date.today()]
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

                chart = fig.to_html()

                context = {
                    'chart': chart,
                    'chart2': chart2,
                    'form': form,
                    'form2': form2
                }

        else:
            # If form not valid or unsubmitted
            # Display unfiltered graph for all dates and show errors
            chart = sp.RunningTotPlotFunctions(
            ).form_not_submitted_or_invalid()

            context = {
                'chart': chart,
                'chart2': chart2,
                'form': form,
                'form2': form2
            }

    else:
        # If form for monthly chart is submitted
        if 'monthly' in request.GET:
            form = DateForm()
            form2 = MonthlyForm(request.GET)
            if form2.is_valid():
                start_month = form2.cleaned_data.get("start_month")
                end_month = form2.cleaned_data.get("end_month")

                # If no months entered
                if start_month == "---" and end_month == "---":

                    # Display last four months
                    chart2 = sp.RunningTotPlotFunctions().monthly_between_dates(
                        start_of_four_months_ago, start_of_next_month
                    )

                    chart = sp.RunningTotPlotFunctions(
                    ).form_not_submitted_or_invalid()

                    context = {
                        'chart': chart,
                        'chart2': chart2,
                        'form': form,
                        'form2': form2
                    }

                else:
                    # If months are entered
                    month_start = f"{start_month}-01"
                    month_end = f"{end_month}-01"
                    # Convert to date obj
                    date_month_end = datetime.strptime(
                        month_end, "%Y-%m-%d"
                    ).date()
                    #Add one month to the end month
                    #So it is first of next month
                    month_end = date_month_end + relativedelta(months=+1)
                    chart2 = sp.RunningTotPlotFunctions().monthly_between_dates(
                        month_start, month_end
                    )

                    # Reset other chart
                    chart = sp.RunningTotPlotFunctions(
                    ).form_not_submitted_or_invalid()

                    context = {
                        'chart': chart,
                        'chart2': chart2,
                        'form': form,
                        'form2': form2
                    }

            else:
                # If monthly form not valid or unsubmitted
                # Display unfiltered graph for all dates and show errors
                chart2 = sp.RunningTotPlotFunctions().monthly_between_dates(
                    start_of_four_months_ago, start_of_next_month
                )

                chart = sp.RunningTotPlotFunctions(
                ).form_not_submitted_or_invalid()

                context = {
                    'chart': chart,
                    'chart2': chart2,
                    'form': form,
                    'form2': form2
                }

        # If no forms submitted display all charges for all dates in db
        else:
            form = DateForm()
            form2 = MonthlyForm()
            chart2 = sp.RunningTotPlotFunctions().monthly_between_dates(
                start_of_four_months_ago, start_of_next_month
            )
            chart = sp.RunningTotPlotFunctions(
            ).form_not_submitted_or_invalid()
            context = {
                'chart': chart,
                'chart2': chart2,
                'form': form,
                'form2': form2
            }

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
            # Get the start + end year-months from form to filter range
            start = form.cleaned_data.get("start")
            end = form.cleaned_data.get("end")

            # If no months are entered
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
                        ).month_range_form_submitted_no_proj_or_assay(
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
                    int(end.split("-")[0]),int(end.split("-")[1])
                )[1]
                month_end = f"{end}-{last_day_of_end_month}"

                # If there are both a project type and assay type entered
                # Get the single string from each
                if (form.cleaned_data.get('project_type') and
                    form.cleaned_data.get('assay_type')):
                    project_type = form.cleaned_data.get('project_type')
                    assay_type = form.cleaned_data.get('assay_type')

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
                        ).month_range_form_submitted_no_proj_or_assay(
                            month_start,
                            month_end,
                            form
                        )

        else:
            # If the form is not valid, display just the standard graph
            # Grouped by last four months
            # For all projects
            context = sp.StoragePlotFunctions(
                ).form_is_not_submitted_or_invalid(form)

    elif 'clear' in request.GET:
        form = StorageForm()
        context = sp.StoragePlotFunctions(
            ).form_is_not_submitted_or_invalid(form)
    else:
        # If nothing is submitted on the form (normal landing page)
        # Display the all projects graph grouped by last four months
        form = StorageForm()
        context = sp.StoragePlotFunctions(
            ).form_is_not_submitted_or_invalid(form)

    # if 'reset' in request.GET:
    #     form = StorageForm(request.GET)
    #     context = sp.StoragePlotFunctions(
    #         ).form_is_not_submitted_or_invalid(form)
    return render(request, 'bar_chart.html', context)


def jobs(request):
    """View to display the jobs data"""
    return render(request, 'jobs.html')
