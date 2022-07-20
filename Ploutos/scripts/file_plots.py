from datetime import date
import numpy as np
import pandas as pd
import plotly.express as px

from dashboard.models import FileTypeDate
from django.db.models import Sum
from scripts.storage_plots import StoragePlotFunctions


sp = StoragePlotFunctions()

class FilePlotFunctions():
    """Functions for the file type storage plots"""

    def __init__(self) -> None:
        # Steal lots of things already defined in StoragePlotFunctions
        self.chart_data = sp.chart_data
        self.proj_colour_dict = sp.proj_colour_dict
        self.assay_colour_dict = sp.assay_colour_dict
        self.project_colours = sp.project_colours
        self.assay_colours = sp.assay_colours

        # Get new colour palette for BAM, FASTQ and VCF
        self.file_type_colours = px.colors.qualitative.Pastel


    def convert_to_df(self, category_chart_data, size_or_count, multi_or_all):
        """
        Convert chart data to a pandas df then convert it to HTML
        So it can be shown below the graph and be easily exported

        Parameters
        ----------
        category_chart_data : dict
            dictionary which has all the chart attributes and data
        size_or_count : str
            string "size" or "count" - whether to make df
            with size or count header
        multi_or_all : str
            string "multi" or "all" - whether all projects
            or looking at specific proj types
        Returns
        -------
        chart_data : pd.DataFrame as HTML table
            dataframe for DataTables
            with Scope, File Type, State and Total Size / Count
        """

        # Make df from the series data
        series_data = category_chart_data['series'].copy()
        exploded = pd.json_normalize(data=series_data).explode('data')

        # Set the column header variable depending on whether size or count df
        if size_or_count == 'size':
            column_title = 'Total Size (TiB)'
        else:
            column_title = 'Total Count'

        # If all projects shown, column order is slightly different to multi
        if multi_or_all == 'all':
            scope = category_chart_data['xAxis']['categories'].copy()

            # If data exists, expand the scope entries according to df length
            # So the correct scope can be added to the right row
            # And add in as column
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
            # Expand file types so they match length of df and add column
            if file_types:
                file_types = file_types * (int(len(exploded) / len(file_types)))
                exploded['File Type'] = file_types
            else:
                file_types = []

            # Re-order columns
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
            justify='center',
        )

        return chart_data


    def file_types_size_all_projects(self, date_to_filter):
        """
        Returns the chart data and a df for today's file sizes in DNAnexus
        For all of the projects aggregated

        Parameters
        ----------
        date_to_filter : str or date object
            date to filter the FileTypeDate objects, is either today default
            or the date which has been entered into the datepicker

        Returns
        -------
        category_chart_data : dict
            size series data and chart options to pass to Highcharts
        chart_df : pd.DataFrame
            dataframe of the series size values to show under chart
        """
        file_type_names = ['bam', 'fastq', 'vcf']
        category_data_source = []
        # Count is -2 and adding 2 because I liked those colours
        count = -2

        for file_type in file_type_names:
            count += 2
            file_type_size = FileTypeDate.objects.filter(
                date__date=date_to_filter,
                file_state__file_type__file_type=file_type
            ).aggregate(
                Live_Size=Sum('file_state__file_size_live'),
                Archived_Size=Sum('file_state__file_size_archived')
            )

            # If there is a summed live size for day, convert to TiB
            # Otherwise leave as empty list
            live_size = file_type_size.get('Live_Size')
            if live_size:
                live_size = [live_size / 1024]
            else:
                live_size = []

            live_data = {
                'name': file_type.upper(),
                'data': live_size,
                'stack': 'Live',
                'color': self.file_type_colours[count]
            }

            # If there is a summed archived size for day, convert to TiB
            # Otherwise leave as empty list
            archived_size = file_type_size.get('Archived_Size')
            if archived_size:
                archived_size = [archived_size / 1024]
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

        # Make project level dataframe so user can see which projs
        # Have all the files
        proj_level_file_type_df = pd.DataFrame.from_records(
            FileTypeDate.objects.filter(
                date__date=date_to_filter
            ).values(
                'project_id__name',
                'file_state__file_type__file_type',
                'file_state__file_size_live',
                'file_state__file_size_archived',
                'file_state__file_count_live',
                'file_state__file_count_archived'
            )
        )

        # If the queryset was empty meaning the df is empty
        # Because script hasn't run today, set final df to empty
        if proj_level_file_type_df.empty:
            one_proj_per_row_file_types = pd.DataFrame()
        else:
            # DataFrame not empty (there is data today)
            proj_level_file_type_df.rename(
                columns={
                    'project_id__name': 'Project',
                    'file_state__file_type__file_type': 'File Type',
                    'file_state__file_size_live': 'Live Size (GiB)',
                    'file_state__file_size_archived': 'Archived Size (GiB)',
                    'file_state__file_count_live': 'Live Count',
                    'file_state__file_count_archived': 'Archived Count'
                }, inplace=True
            )

            proj_level_file_type_df['File Type'] = proj_level_file_type_df[
                'File Type'
            ].str.upper()

            # Get one row per project rather than 3 (one for each file type)
            one_proj_per_row_file_types = proj_level_file_type_df.pivot(
                index='Project',
                columns='File Type',
                values=[
                    'Live Count', 'Archived Count',
                    'Live Size (GiB)', 'Archived Size (GiB)'
                ]
            )

            one_proj_per_row_file_types[
                'Live Count'
            ] = one_proj_per_row_file_types['Live Count'].astype(int)
            one_proj_per_row_file_types[
                'Archived Count'
            ] = one_proj_per_row_file_types['Archived Count'].astype(int)

        # Convert to HTML to easily show with DataTables
        one_proj_per_row_file_types = one_proj_per_row_file_types.to_html(
            classes='table table-striped"',
            justify='center',
            float_format="%.2f"
        )

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = ["All projects"]
        category_chart_data['series'] = category_data_source
        category_chart_data['title']['text'] = (
            f"File Type Sizes - {date_to_filter}"
        )
        category_chart_data['yAxis']['title']['text'] = "Total size (TiB)"
        category_chart_data['tooltip']['pointFormat'] = (
            "{series.name}: <b>{point.y:.2f} TiB </b><br>"
            "{series.options.stack}<br>"
        )

        chart_df = self.convert_to_df(category_chart_data, "size", "all")

        return category_chart_data, chart_df, one_proj_per_row_file_types


    def file_types_count_all_projects(self, date_to_filter):
        """
        Returns the chart data and a df for today's file counts in DNAnexus
        For all of the projects aggregated

        Parameters
        ----------
        date_to_filter : str or date object
            date to filter the FileTypeDate objects, is either today default
            or the date which has been entered into the datepicker

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
                date__date=date_to_filter,
                file_state__file_type__file_type=file_type
            ).aggregate(
                Live_Count=Sum('file_state__file_count_live'),
                Archived_Count=Sum('file_state__file_count_archived')
            )

            # If there is a summed live count for day, get count
            # Otherwise leave as empty list
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

            # If there is a summed archived count for day, get count
            # Otherwise leave as empty list
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
            f"File Type Counts - {date_to_filter}"
        )
        category_chart_data['yAxis']['title']['text'] = "Total count"
        category_chart_data['tooltip']['pointFormat'] = (
            "{series.name}: <b>{point.y:.f}</b><br>"
            "{series.options.stack}<br>"
        )

        chart_df = self.convert_to_df(category_chart_data, "count", "all")

        return category_chart_data, chart_df


    def file_types_count_project_types(self, date_to_filter, proj_types):
        """
        Returns the chart data and a df for today's file counts in DNAnexus
        When only project types have been entered

        Parameters
        ----------
        date_to_filter : str or date object
            date to filter the FileTypeDate objects, is either today default
            or the date which has been entered into the datepicker
        proj_types : list
            list of project types entered in the form e.g. ['001','002']

        Returns
        -------
        category_chart_data : dict
            count series data and chart options to pass to Highcharts
        chart_df : pd.DataFrame
            dataframe of the series count values to show under chart
        """
        file_type_categories_dups = []
        category_data_source = []
        count = -1
        for proj_type in proj_types:
            count += 1
            file_count_list = FileTypeDate.objects.filter(
                date__date=date_to_filter,
                project__name__startswith=proj_type,
            ).values(
                'file_state__file_type__file_type',
                ).annotate(
                    Live_Count=Sum('file_state__file_count_live'),
                    Archived_Count=Sum('file_state__file_count_archived')
            )

            # Get the file types values from the list of querysets
            # This will be multiple lists
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

        # Get only the first list of file type names in the list of lists
        # As all the lists within it will be the same
        file_type_categories = file_type_categories_dups[0]

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = file_type_categories
        category_chart_data['series'] = category_data_source
        category_chart_data['title']['text'] = (
            f"File Counts By Project Type - {date_to_filter}"
        )
        category_chart_data['yAxis']['title']['text'] = "Total Count"
        category_chart_data['tooltip']['pointFormat'] = (
            "{series.name}: <b>{point.y:.0f}</b><br>"
            "{series.options.stack}<br>"
        )

        chart_df = self.convert_to_df(category_chart_data, "count", "multi")

        return category_chart_data, chart_df


    def file_types_size_project_types(self, date_to_filter, proj_types):
        """
        Returns the chart data and a df for today's file sizes in DNAnexus
        When only project types have been entered

        Parameters
        ----------
        date_to_filter : str or date object
            date to filter the FileTypeDate objects, is either today default
            or the date which has been entered into the datepicker
        proj_types : list
            list of project types entered in the form e.g. ['001','002']

        Returns
        -------
        category_chart_data : dict
            size series data and chart options to pass to Highcharts
        chart_df : pd.DataFrame
            dataframe of the series size values to show under chart
        """
        proj_level_file_type_df = pd.DataFrame()
        file_type_categories_dups = []
        category_data_source = []
        count = -1
        for proj_type in proj_types:
            count += 1
            file_size_list = FileTypeDate.objects.filter(
                date__date=date_to_filter,
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
                    (entry.get('Live_Size')/1024)
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
                    (entry.get('Archived_Size')/1024)
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

            # Make project level dataframe so user can see which projs
            # Have all the files
            this_df = pd.DataFrame.from_records(
                FileTypeDate.objects.filter(
                    date__date=date_to_filter,
                    project__name__startswith=proj_type
                ).values(
                    'project_id__name',
                    'file_state__file_type__file_type',
                    'file_state__file_size_live',
                    'file_state__file_size_archived',
                    'file_state__file_count_live',
                    'file_state__file_count_archived'
                )
            )

            proj_level_file_type_df = pd.concat(
                [proj_level_file_type_df, this_df]
            )

        # If the queryset was empty meaning the df is empty
        # Because script hasn't run today, set final df to empty
        if proj_level_file_type_df.empty:
            one_proj_per_row_file_types = pd.DataFrame()
        else:
            # DataFrame not empty (there is data today)
            proj_level_file_type_df.rename(
                columns={
                    'project_id__name': 'Project',
                    'file_state__file_type__file_type': 'File Type',
                    'file_state__file_size_live': 'Live Size (GiB)',
                    'file_state__file_size_archived': 'Archived Size (GiB)',
                    'file_state__file_count_live': 'Live Count',
                    'file_state__file_count_archived': 'Archived Count'
                }, inplace=True
            )

            proj_level_file_type_df['File Type'] = proj_level_file_type_df[
                'File Type'
            ].str.upper()

            # Get one row per project rather than 3 (one for each file type)
            one_proj_per_row_file_types = proj_level_file_type_df.pivot(
                index='Project',
                columns='File Type',
                values=[
                    'Live Count', 'Archived Count',
                    'Live Size (GiB)', 'Archived Size (GiB)'
                ]
            )

            one_proj_per_row_file_types[
                'Live Count'
            ] = one_proj_per_row_file_types['Live Count'].astype(int)
            one_proj_per_row_file_types[
                'Archived Count'
            ] = one_proj_per_row_file_types['Archived Count'].astype(int)

        # Convert to HTML to easily show with DataTables
        one_proj_per_row_file_types = one_proj_per_row_file_types.to_html(
            classes='table table-striped"',
            justify='center',
            float_format="%.2f"
        )

        file_type_categories = file_type_categories_dups[0]
        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = file_type_categories
        category_chart_data['series'] = category_data_source
        category_chart_data['title']['text'] = (
            f"File Sizes By Project Type - {date_to_filter}"
        )
        category_chart_data['yAxis']['title']['text'] = "Total Size"
        category_chart_data['tooltip']['pointFormat'] = (
            "{series.name}: <b>{point.y:.2f} TiB </b><br>"
            "{series.options.stack}<br>"
        )

        chart_df = self.convert_to_df(category_chart_data, "size", "multi")

        return category_chart_data, chart_df, one_proj_per_row_file_types


    def file_types_count_assay_types(self, date_to_filter, assay_types):
        """
        Returns the chart data and a df for today's file counts in DNAnexus
        When only assay types have been entered

        Parameters
        ----------
        date_to_filter : str or date object
            date to filter the FileTypeDate objects, is either today default
            or the date which has been entered into the datepicker
        assay_types : list
            list of project types entered in the form e.g. ['CEN','TWE']

        Returns
        -------
        category_chart_data : dict
            count series data and chart options to pass to Highcharts
        chart_df : pd.DataFrame
            dataframe of the series count values to show under chart
        """
        file_type_categories_dups = []
        category_data_source = []
        count = -1
        for assay_type in assay_types:
            count += 1
            file_count_list = FileTypeDate.objects.filter(
                date__date=date_to_filter,
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
            f"File Counts By Assay Type - {date_to_filter}"
        )
        category_chart_data['yAxis']['title']['text'] = "Total Count"
        category_chart_data['tooltip']['pointFormat'] = (
            "{series.name}: <b>{point.y:.0f} </b><br>"
            "{series.options.stack}<br>"
        )

        chart_df = self.convert_to_df(category_chart_data, "count", "multi")

        return category_chart_data, chart_df


    def file_types_size_assay_types(self, date_to_filter, assay_types):
        """
        Returns the chart data and a df for today's file sizes in DNAnexus
        When only assay types have been entered

        Parameters
        ----------
        date_to_filter : str or date object
            date to filter the FileTypeDate objects, is either today default
            or the date which has been entered into the datepicker
        assay_types : list
            list of project types entered in the form e.g. ['CEN','TWE']

        Returns
        -------
        category_chart_data : dict
            size series data and chart options to pass to Highcharts
        chart_df : pd.DataFrame
            dataframe of the series size values to show under chart
        """
        proj_level_file_type_df = pd.DataFrame()
        file_type_categories_dups = []
        category_data_source = []
        count = -1
        for assay_type in assay_types:
            count += 1
            file_size_list = FileTypeDate.objects.filter(
                date__date=date_to_filter,
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
                    (entry.get('Live_Size')/1024)
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
                    (entry.get('Archived_Size')/1024)
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

            # Make project level dataframe so user can see which projs
            # Have all the files
            this_df = pd.DataFrame.from_records(
                FileTypeDate.objects.filter(
                    date__date=date_to_filter,
                    project__name__endswith=assay_type
                ).values(
                    'project_id__name',
                    'file_state__file_type__file_type',
                    'file_state__file_size_live',
                    'file_state__file_size_archived',
                    'file_state__file_count_live',
                    'file_state__file_count_archived'
                )
            )

            proj_level_file_type_df = pd.concat(
                [proj_level_file_type_df, this_df]
            )

        # If the queryset was empty meaning the df is empty
        # Because script hasn't run today, set final df to empty
        if proj_level_file_type_df.empty:
            one_proj_per_row_file_types = pd.DataFrame()
        else:
            # DataFrame not empty (there is data today)
            proj_level_file_type_df.rename(
                columns={
                    'project_id__name': 'Project',
                    'file_state__file_type__file_type': 'File Type',
                    'file_state__file_size_live': 'Live Size (GiB)',
                    'file_state__file_size_archived': 'Archived Size (GiB)',
                    'file_state__file_count_live': 'Live Count',
                    'file_state__file_count_archived': 'Archived Count'
                }, inplace=True
            )
            proj_level_file_type_df['File Type'] = proj_level_file_type_df[
                'File Type'
            ].str.upper()

            # Get one row per project rather than 3 (one for each file type)
            one_proj_per_row_file_types = proj_level_file_type_df.pivot(
                index='Project',
                columns='File Type',
                values=[
                    'Live Count', 'Archived Count',
                    'Live Size (GiB)', 'Archived Size (GiB)'
                ]
            )

            one_proj_per_row_file_types[
                'Live Count'
            ] = one_proj_per_row_file_types['Live Count'].astype(int)
            one_proj_per_row_file_types[
                'Archived Count'
            ] = one_proj_per_row_file_types['Archived Count'].astype(int)

        # Convert to HTML to easily show with DataTables
        one_proj_per_row_file_types = one_proj_per_row_file_types.to_html(
            classes='table table-striped"',
            justify='center',
            float_format="%.2f"
        )

        file_type_categories = file_type_categories_dups[0]

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = file_type_categories
        category_chart_data['series'] = category_data_source
        category_chart_data['title']['text'] = (
            f"File Sizes By Assay Type - {date_to_filter}"
        )
        category_chart_data['yAxis']['title']['text'] = "Total Size (TiB)"
        category_chart_data['tooltip']['pointFormat'] = (
            "{series.name}: <b>{point.y:.2f} TiB</b><br>"
            "{series.options.stack}<br>"
        )

        chart_df = self.convert_to_df(category_chart_data, "size", "multi")

        return category_chart_data, chart_df, one_proj_per_row_file_types


    def file_types_count_assay_and_proj_types(
        self, date_to_filter, project_type, assay_type
    ):
        """
        Returns the chart data and a df for today's file counts in DNAnexus
        When a project type and an assay type has been entered

        Parameters
        ----------
        date_to_filter : str or date object
            date to filter the FileTypeDate objects, is either today default
            or the date which has been entered into the datepicker
        project_type : str
            what the project name begins with e.g. "002"
        assay_type : str
            what the project name ends with e.g. "CEN"

        Returns
        -------
        category_chart_data : dict
            count series data and chart options to pass to Highcharts
        chart_df : pd.DataFrame
            dataframe of the series count values to show under chart
        """
        category_data_source = []
        file_count_list = FileTypeDate.objects.filter(
            date__date=date_to_filter,
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
            f"File Counts By Project + Assay Type - {date_to_filter}"
        )
        category_chart_data['yAxis']['title']['text'] = "Total Count"
        category_chart_data['tooltip']['pointFormat'] = (
            "{series.name}: <b>{point.y:.0f}</b><br>"
            "{series.options.stack}<br>"
        )

        chart_df = self.convert_to_df(category_chart_data, "count", "multi")

        return category_chart_data, chart_df


    def file_types_size_assay_and_proj_types(
        self, date_to_filter, project_type, assay_type
    ):
        """
        Returns the chart data and a df for today's file sizes in DNAnexus
        When a project type and an assay type has been entered

        Parameters
        ----------
        date_to_filter : str or date object
            date to filter the FileTypeDate objects, is either today default
            or the date which has been entered into the datepicker
        project_type : str
            what the project name begins with e.g. "002"
        assay_type : str
            what the project name ends with e.g. "CEN"

        Returns
        -------
        category_chart_data : dict
            size series data and chart options to pass to Highcharts
        chart_df : pd.DataFrame
            dataframe of the series size values to show under chart
        """
        category_data_source = []
        file_size_list = FileTypeDate.objects.filter(
            date__date=date_to_filter,
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
                (entry.get('Live_Size')/1024)
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
                (entry.get('Archived_Size')/1024)
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

        # Make project level dataframe so user can see which projs
        # Have all the files
        proj_level_file_type_df = pd.DataFrame.from_records(
            FileTypeDate.objects.filter(
                date__date=date_to_filter,
                project__name__startswith=project_type,
                project__name__endswith=assay_type
            ).values(
                'project_id__name',
                'file_state__file_type__file_type',
                'file_state__file_size_live',
                'file_state__file_size_archived',
                'file_state__file_count_live',
                'file_state__file_count_archived'
            )
        )

        # If the queryset was empty meaning the df is empty
        # Because script hasn't run today, set final df to empty
        if proj_level_file_type_df.empty:
            one_proj_per_row_file_types = pd.DataFrame()
        else:
            # DataFrame not empty (there is data today)
            proj_level_file_type_df.rename(
                columns={
                    'project_id__name': 'Project',
                    'file_state__file_type__file_type': 'File Type',
                    'file_state__file_size_live': 'Live Size (GiB)',
                    'file_state__file_size_archived': 'Archived Size (GiB)',
                    'file_state__file_count_live': 'Live Count',
                    'file_state__file_count_archived': 'Archived Count'
                }, inplace=True
            )

            proj_level_file_type_df['File Type'] = proj_level_file_type_df[
                'File Type'
            ].str.upper()

            # Get one row per project rather than 3 (one for each file type)
            one_proj_per_row_file_types = proj_level_file_type_df.pivot(
                index='Project',
                columns='File Type',
                values=[
                    'Live Count', 'Archived Count',
                    'Live Size (GiB)', 'Archived Size (GiB)'
                ]
            )

            one_proj_per_row_file_types[
                'Live Count'
            ] = one_proj_per_row_file_types['Live Count'].astype(int)
            one_proj_per_row_file_types[
                'Archived Count'
            ] = one_proj_per_row_file_types['Archived Count'].astype(int)

        # Convert to HTML to easily show with DataTables
        one_proj_per_row_file_types = one_proj_per_row_file_types.to_html(
            classes='table table-striped"',
            justify='center',
            float_format="%.2f"
        )

        category_chart_data = self.chart_data.copy()
        category_chart_data['xAxis']['categories'] = file_type_categories
        category_chart_data['series'] = category_data_source
        category_chart_data['title']['text'] = (
            f"File Sizes By Project + Assay Type - {date_to_filter}"
        )
        category_chart_data['yAxis']['title']['text'] = "Total Size (TiB)"
        category_chart_data['tooltip']['pointFormat'] = (
            "{series.name}: <b>{point.y:.2f} TiB</b><br>"
            "{series.options.stack}<br>"
        )

        chart_df = self.convert_to_df(category_chart_data, "size", "multi")

        return category_chart_data, chart_df, one_proj_per_row_file_types
