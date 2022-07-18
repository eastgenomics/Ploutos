import pandas as pd
import plotly.express as px

from more_itertools import unique_everseen

from dashboard.models import FileTypeDate
from django.db.models import Sum
from scripts import storage_plots as sp

class FilePlotFunctions():
    """Functions for the file type storage plots"""

    def __init__(self) -> None:
        self.today_date = sp.StoragePlotFunctions().today_date
        self.file_type_colours = px.colors.qualitative.Pastel
        # Chart data which is shared by all plots
        self.chart_data = sp.StoragePlotFunctions().chart_data
        self.file_type_objs = FileTypeDate.objects.all()
        self.proj_colour_dict = sp.StoragePlotFunctions().proj_colour_dict
        self.assay_colour_dict = sp.StoragePlotFunctions().assay_colour_dict
        self.project_colours = sp.StoragePlotFunctions().project_colours
        self.assay_colours = sp.StoragePlotFunctions().assay_colours
        self.file_type_categories = ['VCF', 'FASTQ', 'BAM']

    def convert_to_df(self, category_chart_data, size_or_count, multi_or_all):
        """
        Convert chart data to a pandas df then convert it to HTML
        So it can be shown below the graph and be easily exported

        Parameters
        ----------
        category_chart_data : dict
            dictionary which has all the chart attributes and data
        size_or_count : str
            a string to say whether to make a df for size or count
        multi_or_all : str
            a string to say whether all projects or looking at specific types
        Returns
        -------
        chart_data : pd.DataFrame as HTML table
            the dataframe with Date, Type, State and Total Size
        """
        series_data = category_chart_data['series'].copy()
        exploded = pd.json_normalize(data=series_data).explode('data')

        if size_or_count == 'size':
            column_title = 'Total Size (GiB)'
        else:
            column_title = 'Total Count'

        if multi_or_all == 'all':
            scope = category_chart_data['xAxis']['categories'].copy()

            # If data exists, expand the dates table according to the df length
            # So the correct date can be added to the right row
            if scope:
                scope = scope * (int(len(exploded) / len(scope)))
                exploded['Scope'] = scope
            else:
                scope = []

            # Re-order columns
            exploded = exploded.reindex(
                columns=[
                    'Scope', 'name', 'stack', 'data'
                ]
            )

            exploded.rename(
                columns={
                    "name": "File Type",
                    "stack": "State",
                    'data': column_title
                },
                inplace = True
            )
        elif multi_or_all == 'multi':
            # If looking at multiple diff proj / assay types
            file_types = category_chart_data['xAxis']['categories'].copy()
            if file_types:
                file_types = file_types * (int(len(exploded) / len(file_types)))
                exploded['File Type'] = file_types
            else:
                file_types = []

            exploded = exploded.reindex(
                columns=[
                    'name', 'File Type', 'stack', 'data'
                ]
            )

            exploded.rename(
                columns={
                    "name": "Scope",
                    "stack": "State",
                    'data': column_title
                },
                inplace = True
            )

        # Convert to HTML to easily show with DataTables
        chart_data = exploded.to_html(
            index=False,
            classes='table table-striped"',
            justify='left'
        )

        return chart_data

    def todays_file_types_size_all_projects(self):
        """
        Returns the chart data and a df for today's file sizes in DNAnexus
        For all of the projects aggregated

        Parameters
        ----------
        none

        Returns
        -------
        category_chart_data : dict
            size series data and chart options to pass to Highcharts
        chart_df : pd.DataFrame
            dataframe of the series size values to show under chart
        """
        file_type_names = ['bam', 'fastq', 'vcf']

        category_data_source = []
        count = -2
        for file_type in file_type_names:
            count += 2
            file_type_size = FileTypeDate.objects.filter(
                date__date=self.today_date,
                file_state__file_type__file_type=file_type
            ).aggregate(
                Live_Size=Sum('file_state__file_size_live'),
                Archived_Size=Sum('file_state__file_size_archived')
            )

            live_size = file_type_size.get('Live_Size')
            if live_size:
                live_size = [live_size / (2**30)]
            else:
                live_size = []

            live_data = {
                'name': file_type.upper(),
                'data': live_size,
                'stack': 'Live',
                'color': self.file_type_colours[count]
            }

            archived_size = file_type_size.get('Archived_Size')
            if archived_size:
                archived_size = [archived_size / (2**30)]
            else:
                archived_size = []

            archived_data = {
                'name': file_type.upper(),
                'data': archived_size,
                'stack': 'Archived',
                'linkedTo': ':previous',
                'color': self.file_type_colours[count],
                'opacity': 0.8
            }

            category_data_source.append(live_data)
            category_data_source.append(archived_data)

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = ["All projects"]
        category_chart_data['series'] = category_data_source
        category_chart_data['title']['text'] = (
            f"Today's File Type Sizes - {self.today_date}"
        )
        category_chart_data['yAxis']['title']['text'] = "Total size (GiB)"
        category_chart_data['tooltip']['pointFormat'] = (
            "{series.name}: <b>{point.y:.2f} GiB </b><br>"
            "{series.options.stack}<br>"
        )

        chart_df = self.convert_to_df(category_chart_data, "size", "all")

        return category_chart_data, chart_df

    def todays_file_types_count_all_projects(self):
        """
        Returns the chart data and a df for today's file counts in DNAnexus
        For all of the projects aggregated

        Parameters
        ----------
        none

        Returns
        -------
        category_chart_data : dict
            count series data and chart options to pass to Highcharts
        chart_df : pd.DataFrame
            dataframe of the series count values to show under chart
        """
        file_type_names = ['bam','fastq','vcf']

        category_data_source = []
        count = -2
        for file_type in file_type_names:
            count += 2
            file_type_size = FileTypeDate.objects.filter(
                date__date=self.today_date,
                file_state__file_type__file_type=file_type
            ).aggregate(
                Live_Count=Sum('file_state__file_count_live'),
                Archived_Count=Sum('file_state__file_count_archived')
            )

            live_count = file_type_size.get('Live_Count')
            if live_count:
                live_count = [live_count]
            else:
                live_count = []

            live_data = {
                'name': file_type.upper(),
                'data': live_count,
                'stack': 'Live',
                'color': self.file_type_colours[count]
            }

            archived_count = file_type_size.get('Archived_Count')
            if archived_count:
                archived_count = [archived_count]
            else:
                archived_count = []

            archived_data = {
                'name': file_type.upper(),
                'data': archived_count,
                'stack': 'Archived',
                'linkedTo': ':previous',
                'color': self.file_type_colours[count],
                'opacity': 0.8
            }

            category_data_source.append(live_data)
            category_data_source.append(archived_data)

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = ["All projects"]
        category_chart_data['series'] = category_data_source
        category_chart_data['title']['text'] = (
            f"Today's File Type Counts - {self.today_date}"
        )
        category_chart_data['yAxis']['title']['text'] = "Total count"
        category_chart_data['tooltip']['pointFormat'] = (
            "{series.name}: <b>{point.y:.f}</b><br>"
            "{series.options.stack}<br>"
        )

        chart_df = self.convert_to_df(category_chart_data, "count", "all")

        return category_chart_data, chart_df

    def todays_file_types_count_project_types(self, proj_types):
        """DO DOCSTRING"""
        file_type_categories_dups = []
        category_data_source = []
        count = -1
        for proj_type in proj_types:
            count += 1
            file_count_list = self.file_type_objs.filter(
                date__date=self.today_date,
                project__name__startswith=proj_type,
            ).values(
                'file_state__file_type__file_type',
                ).annotate(
                    Live_Count=Sum('file_state__file_count_live'),
                    Archived_Count=Sum('file_state__file_count_archived')
            )

            file_types = [
                entry.get('file_state__file_type__file_type').upper()
                for entry in file_count_list
            ]

            live_data = {
                'name': f"{proj_type}*",
                'data': [
                    entry.get('Live_Count') for entry in file_count_list
                ],
                'stack': 'Live',
                'color': self.proj_colour_dict.get(
                    proj_type, self.project_colours[count]
                )
            }

            archived_data = {
                'name': f"{proj_type}*",
                'data': [
                    entry.get('Archived_Count') for entry in file_count_list
                ],
                'stack': 'Archived',
                'linkedTo': ':previous',
                'color': self.proj_colour_dict.get(
                    proj_type, self.project_colours[count]
                ),
                'opacity': 0.8
            }

            category_data_source.append(live_data)
            category_data_source.append(archived_data)
            file_type_categories_dups.append(file_types)

        file_type_categories = file_type_categories_dups[0]

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = file_type_categories
        category_chart_data['series'] = category_data_source
        category_chart_data['title']['text'] = (
            f"Today's File Counts By Project Type - {self.today_date}"
        )
        category_chart_data['yAxis']['title']['text'] = "Total Count"
        category_chart_data['tooltip']['pointFormat'] = (
            "{series.name}: <b>{point.y:.0f}</b><br>"
            "{series.options.stack}<br>"
        )

        chart_df = self.convert_to_df(category_chart_data, "count", "multi")

        return category_chart_data, chart_df

    def todays_file_types_size_project_types(self, proj_types):
        """DO DOCSTRING"""
        file_type_categories_dups = []
        category_data_source = []
        count = -1
        for proj_type in proj_types:
            count += 1
            file_size_list = self.file_type_objs.filter(
                date__date=self.today_date,
                project__name__startswith=proj_type,
            ).values(
                'file_state__file_type__file_type',
                ).annotate(
                    Live_Size=Sum('file_state__file_size_live'),
                    Archived_Size=Sum('file_state__file_size_archived')
            )

            file_types = [
                entry.get('file_state__file_type__file_type').upper()
                for entry in file_size_list
            ]

            live_data = {
                'name': f"{proj_type}*",
                'data': [
                    (entry.get('Live_Size')/(2**30))
                    for entry in file_size_list
                ],
                'stack': 'Live',
                'color': self.proj_colour_dict.get(
                    proj_type, self.project_colours[count]
                )
            }

            archived_data = {
                'name': f"{proj_type}*",
                'data': [
                    (entry.get('Archived_Size')/(2**30))
                    for entry in file_size_list
                ],
                'stack': 'Archived',
                'linkedTo': ':previous',
                'color': self.proj_colour_dict.get(
                    proj_type, self.project_colours[count]
                ),
                'opacity': 0.8
            }

            category_data_source.append(live_data)
            category_data_source.append(archived_data)
            file_type_categories_dups.append(file_types)

        file_type_categories = file_type_categories_dups[0]

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = file_type_categories
        category_chart_data['series'] = category_data_source
        category_chart_data['title']['text'] = (
            f"Today's File Sizes By Project Type - {self.today_date}"
        )
        category_chart_data['yAxis']['title']['text'] = "Total Size"
        category_chart_data['tooltip']['pointFormat'] = (
            "{series.name}: <b>{point.y:.2f} GiB </b><br>"
            "{series.options.stack}<br>"
        )

        chart_df = self.convert_to_df(category_chart_data, "size", "multi")

        return category_chart_data, chart_df

    def todays_file_types_count_assay_types(self, assay_types):
        """DO DOCSTRING"""
        file_type_categories_dups = []
        category_data_source = []
        count = -1
        for assay_type in assay_types:
            count += 1
            file_count_list = self.file_type_objs.filter(
                date__date=self.today_date,
                project__name__endswith=assay_type,
            ).values(
                'file_state__file_type__file_type',
            ).annotate(
                    Live_Count=Sum('file_state__file_count_live'),
                    Archived_Count=Sum('file_state__file_count_archived')
            )

            file_types = [
                entry.get('file_state__file_type__file_type').upper()
                for entry in file_count_list
            ]

            live_data = {
                'name': f"*{assay_type}",
                'data': [
                    entry.get('Live_Count')
                    for entry in file_count_list
                ],
                'stack': 'Live',
                'color': self.assay_colour_dict.get(
                    assay_type, self.assay_colours[count]
                )
            }

            archived_data = {
                'name': f"*{assay_type}",
                'data': [
                    entry.get('Archived_Count')
                    for entry in file_count_list
                ],
                'stack': 'Archived',
                'linkedTo': ':previous',
                'color': self.assay_colour_dict.get(
                    assay_type, self.assay_colours[count]
                ),
                'opacity': 0.8
            }

            category_data_source.append(live_data)
            category_data_source.append(archived_data)
            file_type_categories_dups.append(file_types)

        file_type_categories = file_type_categories_dups[0]

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = file_type_categories
        category_chart_data['series'] = category_data_source
        category_chart_data['title']['text'] = (
            f"Today's File Counts By Assay Type - {self.today_date}"
        )
        category_chart_data['yAxis']['title']['text'] = "Total Count"
        category_chart_data['tooltip']['pointFormat'] = (
            "{series.name}: <b>{point.y:.0f} </b><br>"
            "{series.options.stack}<br>"
        )

        chart_df = self.convert_to_df(category_chart_data, "count", "multi")

        return category_chart_data, chart_df

    def todays_file_types_size_assay_types(self, assay_types):
        """DO DOCSTRING"""
        file_type_categories_dups = []
        category_data_source = []
        count = -1
        for assay_type in assay_types:
            count += 1
            file_size_list = self.file_type_objs.filter(
                date__date=self.today_date,
                project__name__endswith=assay_type,
            ).values(
                'file_state__file_type__file_type',
            ).annotate(
                    Live_Size=Sum('file_state__file_size_live'),
                    Archived_Size=Sum('file_state__file_size_archived')
            )

            file_types = [
                entry.get('file_state__file_type__file_type').upper()
                for entry in file_size_list
            ]

            live_data = {
                'name': f"*{assay_type}",
                'data': [
                    (entry.get('Live_Size')/(2**30))
                    for entry in file_size_list
                ],
                'stack': 'Live',
                'color': self.assay_colour_dict.get(
                    assay_type, self.assay_colours[count]
                )
            }

            archived_data = {
                'name': f"*{assay_type}",
                'data': [
                    (entry.get('Archived_Size')/(2**30))
                    for entry in file_size_list
                ],
                'stack': 'Archived',
                'linkedTo': ':previous',
                'color': self.assay_colour_dict.get(
                    assay_type, self.assay_colours[count]
                ),
                'opacity': 0.8
            }

            category_data_source.append(live_data)
            category_data_source.append(archived_data)
            file_type_categories_dups.append(file_types)

        file_type_categories = file_type_categories_dups[0]

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = file_type_categories
        category_chart_data['series'] = category_data_source
        category_chart_data['title']['text'] = (
            f"Today's File Sizes By Assay Type - {self.today_date}"
        )
        category_chart_data['yAxis']['title']['text'] = "Total Size (GiB)"
        category_chart_data['tooltip']['pointFormat'] = (
            "{series.name}: <b>{point.y:.2f} GiB</b><br>"
            "{series.options.stack}<br>"
        )

        chart_df = self.convert_to_df(category_chart_data, "size", "multi")

        return category_chart_data, chart_df

    def todays_file_types_count_assay_and_proj_types(
        self, project_type, assay_type
    ):
        """DO DOCSTRING"""
        category_data_source = []
        file_count_list = self.file_type_objs.filter(
            date__date=self.today_date,
            project__name__startswith=project_type,
            project__name__endswith=assay_type
        ).values(
            'file_state__file_type__file_type',
        ).annotate(
                Live_Count=Sum('file_state__file_count_live'),
                Archived_Count=Sum('file_state__file_count_archived')
        )

        file_type_categories = [
            entry.get('file_state__file_type__file_type').upper()
            for entry in file_count_list
        ]

        live_data = {
            'name': f"{project_type}*{assay_type}",
            'data': [
                entry.get('Live_Count')
                for entry in file_count_list
            ],
            'stack': 'Live',
            'color': self.proj_colour_dict.get(
                project_type, self.project_colours[0]
            ),
        }

        archived_data = {
            'name': f"{project_type}*{assay_type}",
            'data': [
                entry.get('Archived_Count')
                for entry in file_count_list
            ],
            'stack': 'Archived',
            'linkedTo': ':previous',
            'color': self.proj_colour_dict.get(
                project_type, self.project_colours[0]
            ),
            'opacity': 0.8
        }

        category_data_source.append(live_data)
        category_data_source.append(archived_data)

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = file_type_categories
        category_chart_data['series'] = category_data_source
        category_chart_data['title']['text'] = (
            f"Today's File Counts By Project + Assay Type - {self.today_date}"
        )
        category_chart_data['yAxis']['title']['text'] = "Total Count"
        category_chart_data['tooltip']['pointFormat'] = (
            "{series.name}: <b>{point.y:.0f}</b><br>"
            "{series.options.stack}<br>"
        )

        chart_df = self.convert_to_df(category_chart_data, "count", "multi")

        return category_chart_data, chart_df

    def todays_file_types_size_assay_and_proj_types(
        self, project_type, assay_type
    ):
        """DO DOCSTRING"""
        category_data_source = []
        file_size_list = self.file_type_objs.filter(
            date__date=self.today_date,
            project__name__startswith=project_type,
            project__name__endswith=assay_type
        ).values(
            'file_state__file_type__file_type',
        ).annotate(
                Live_Size=Sum('file_state__file_size_live'),
                Archived_Size=Sum('file_state__file_size_archived')
        )

        file_type_categories = [
            entry.get('file_state__file_type__file_type').upper()
            for entry in file_size_list
        ]

        live_data = {
            'name': f"{project_type}*{assay_type}",
            'data': [
                (entry.get('Live_Size')/(2**30))
                for entry in file_size_list
            ],
            'stack': 'Live',
            'color': self.proj_colour_dict.get(
                project_type, self.project_colours[0]
            ),
        }

        archived_data = {
            'name': f"{project_type}*{assay_type}",
            'data': [
                (entry.get('Archived_Size')/(2**30))
                for entry in file_size_list
            ],
            'stack': 'Archived',
            'linkedTo': ':previous',
            'color': self.proj_colour_dict.get(
                project_type, self.project_colours[0]
            ),
            'opacity': 0.8
        }

        category_data_source.append(live_data)
        category_data_source.append(archived_data)

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = file_type_categories
        category_chart_data['series'] = category_data_source
        category_chart_data['title']['text'] = (
            f"Today's File Sizes By Project + Assay Type - {self.today_date}"
        )
        category_chart_data['yAxis']['title']['text'] = "Total Size (GiB)"
        category_chart_data['tooltip']['pointFormat'] = (
            "{series.name}: <b>{point.y:.2f} GiB</b><br>"
            "{series.options.stack}<br>"
        )

        chart_df = self.convert_to_df(category_chart_data, "size", "multi")

        return category_chart_data, chart_df
