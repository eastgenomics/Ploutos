from django.shortcuts import render
import plotly.express as px
from dashboard.forms import DateForm
from dashboard.models import Users, Projects, Dates, DailyOrgRunningTotal
import datetime

# Create your views here.

# Create your views here.

def index(request):
    """ 
    View to display running total charges via Plotly 
    """
    # Get start and end from form
    start = request.GET.get('start')
    end = request.GET.get('end')

    # Get all totals objs
    totals = DailyOrgRunningTotal.objects.all()

    # Filter totals based on the dates provided in start and end (foreign key)
    if start:
        totals = totals.filter(date__id__in = (Dates.objects.filter(date__range=[start,end]).values_list('id',flat=True)))

    # Stuff to work out delta of storage compared to day before
    # my_date = "2022-04-25"
    # ref_date = datetime.datetime.strptime(my_date, "%Y-%m-%d")
    # day_before = (ref_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    # first_value = Totals.objects.get(date = (Dates.objects.get(date = my_date)).id).storage_charges
    # second_value = Totals.objects.get(date = (Dates.objects.get(date = day_before)).id).storage_charges

    #Storage charges for april
    #DailyOrgRunningTotal.objects.filter(date__id__in=(Dates.objects.filter(date__month=month).values_list('id',flat=True))).aggregate(avg=Avg('storage_charges'))

    # Plot the date and storage charges as line graph
    
    fig = px.line(
        x= [x.date.date for x in totals],
        #x=[Dates.objects.get(id = c.id).date for c in totals],
        y=[[c.compute_charges for c in totals],[c.storage_charges for c in totals],[c.egress_charges for c in totals]],
        title = "Running compute charge total",
        labels = {'x':'Date', 'y':'Compute charge'}
    )

    # Change formatting of title
    fig.update_layout(
        title={
            'font_size': 24,
            'xanchor': 'center',
            'x': 0.5
    })

    chart = fig.to_html()
    context = {'chart': chart, 'form': DateForm()}
    return render(request, 'index.html', context)

def bar_chart(request):
    """Testing a bar chart simply from count of different project types"""
    proj_types = ["001", "002", "003", "004"]
    count = [Projects.objects.filter(name__startswith=type).count() for type in proj_types]

    fig = px.bar(x=proj_types,y=count)
    fig.update_layout(title_text ="Test")

    chart = fig.to_html()
    context = {'chart': chart}
    return render(request, 'index.html', context)
