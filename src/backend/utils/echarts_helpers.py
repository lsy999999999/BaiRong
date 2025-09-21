from typing import Dict, Any, List

# --- ECharts Option Helpers ---

# def create_line_chart_option(title: str, x_axis_data: List[str], series_data: List[Any], series_name: str = "Value") -> Dict[str, Any]:
#     """Creates a basic ECharts line chart option."""
#     # Add default empty list if data is None to avoid frontend errors
#     x_axis_data = x_axis_data if x_axis_data is not None else []
#     series_data = series_data if series_data is not None else []
    
#     return {
#         "title": {"text": title, "left": "center"},
#         "tooltip": {"trigger": "axis"},
#         "legend": {"data": [series_name], "bottom": 10},
#         "grid": {"left": '3%', "right": '4%', "bottom": '10%', "containLabel": True},
#         "xAxis": {"type": "category", "boundaryGap": False, "data": x_axis_data},
#         "yAxis": {"type": "value"},
#         "series": [{"name": series_name, "type": "line", "data": series_data}]
#     }

# def create_pie_chart_option(title: str, series_data: List[Dict[str, Any]], series_name: str = "Distribution") -> Dict[str, Any]:
#     """Creates a basic ECharts pie chart option."""
#     # Add default empty list if data is None
#     series_data = series_data if series_data is not None else []
    
#     return {
#         "title": {"text": title, "left": "center"},
#         "tooltip": {"trigger": "item"},
#         "legend": {"orient": "vertical", "left": "left", "top": "middle"},
#          "series": [{
#             "name": series_name,
#             "type": "pie",
#             "radius": ["40%", "70%"], # Make it a donut chart
#             "avoidLabelOverlap": False,
#             "itemStyle": {
#                 "borderRadius": 10,
#                 "borderColor": '#fff',
#                 "borderWidth": 2
#             },
#             "label": {
#                 "show": False,
#                 "position": 'center'
#             },
#             "emphasis": {
#                 "label": {
#                     "show": True,
#                     "fontSize": '20', # Smaller font size for emphasis
#                     "fontWeight": 'bold'
#                 }
#             },
#             "labelLine": {
#                 "show": False
#             },
#             "data": series_data # Expects data in format [{"name": "...", "value": ...}, ...]
#         }]
#     }

# # Potential helper for Bar chart if needed
# def create_bar_chart_option(title: str, x_axis_data: List[str], series_data: List[Any], series_name: str = "Value") -> Dict[str, Any]:
#     """Creates a basic ECharts bar chart option."""
#     x_axis_data = x_axis_data if x_axis_data is not None else []
#     series_data = series_data if series_data is not None else []
#     # Ensure series_data is in the format ECharts expects: [{name: ..., type: 'bar', data: [...]}, ...]
#     # This helper currently assumes a single series is passed as a list of values.
#     if not series_data or not isinstance(series_data[0], dict):
#         series_list = [{
#             "name": series_name,
#             "type": "bar",
#             "data": series_data
#         }]
#         legend_data = [series_name]
#     else:
#         # If series_data is already a list of dicts (e.g., multiple series)
#         series_list = series_data 
#         legend_data = [s.get('name', f'Series {i+1}') for i, s in enumerate(series_list)]
        
#     return {
#         "title": {"text": title, "left": "center"},
#         "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
#         "legend": {"data": legend_data, "bottom": 10},
#         "grid": {"left": '3%', "right": '4%', "bottom": '10%', "containLabel": True},
#         "xAxis": {"type": "category", "data": x_axis_data},
#         "yAxis": {"type": "value"},
#         "series": series_list # Use the processed list of series objects
#     }

# def create_time_series_chart_option(title: str, series_list: List[Dict[str, Any]]) -> Dict[str, Any]:
#     """Creates an ECharts option optimized for time-series line charts."""
#     # Ensure series_list is valid
#     series_list = series_list if series_list is not None else []
    
#     # Prepare legend data from series names
#     legend_data = [s.get('name', f'Series {i+1}') for i, s in enumerate(series_list)]
    
#     # Modify series for time-series display (e.g., hide symbols)
#     for s in series_list:
#         s["showSymbol"] = False # Hide symbols for cleaner look
#         s["type"] = "line" # Ensure type is line
#         # Data should be in format [[timestamp, value], ...] for time axis
#         # TimeSeriesMetricData.get_echarts_data needs to be adjusted if not already returning this format.
#         # Assuming TimeSeriesMetricData returns series with data: List[Any] and xAxis: List[str/datetime]
#         # We need to combine them for the time axis format.
#         # This helper currently ASSUMES the input series_list data format is already correct for type: 'time'
#         # e.g., series_list = [{'name': '...', 'type': 'line', 'data': [[timestamp1, value1], [timestamp2, value2], ...]}]
        
#     return {
#         "title": {"text": title, "left": "center"},
#         "tooltip": {
#             "trigger": "axis",
#             "axisPointer": {
#                 "animation": False
#             }
#         },
#         "legend": {"data": legend_data, "bottom": 10, "type": "scroll"},
#         "grid": {"left": '5%', "right": '5%', "bottom": '10%', "containLabel": True}, # Adjusted grid slightly
#         "xAxis": {
#             "type": 'time',
#             "splitLine": { "show": False }
#         },
#         "yAxis": {
#             "type": 'value',
#             "boundaryGap": False, # Match user request
#             "splitLine": { "show": False }
#         },
#         "series": series_list # Use the potentially modified series list
#     }



def create_line_chart_option(title: str, x_axis_data: List[str], series_data: List[Any], series_name: str = "Value") -> Dict[str, Any]:
    """Creates a minimal ECharts line chart option with only essential data."""
    x_axis_data = x_axis_data if x_axis_data is not None else []
    series_data = series_data if series_data is not None else []
    
    return {
        "xAxis": {"data": x_axis_data},
        "series": [{"name": series_name, "type": "line", "data": series_data}]
    }

def create_pie_chart_option(title: str, series_data: List[Dict[str, Any]], series_name: str = "Distribution") -> Dict[str, Any]:
    """Creates a minimal ECharts pie chart option with only essential data."""
    series_data = series_data if series_data is not None else []
    
    return {
        "series": [{
            "name": series_name,
            "type": "pie",
            "data": series_data
        }]
    }

def create_bar_chart_option(title: str, x_axis_data: List[str], series_data: List[Any], series_name: str = "Value") -> Dict[str, Any]:
    """Creates a minimal ECharts bar chart option with only essential data."""
    x_axis_data = x_axis_data if x_axis_data is not None else []
    series_data = series_data if series_data is not None else []
    
    if not series_data or not isinstance(series_data[0], dict):
        series_list = [{
            "name": series_name,
            "type": "bar",
            "data": series_data
        }]
    else:
        series_list = series_data
        
    return {
        "xAxis": {"data": x_axis_data},
        "series": series_list
    }

def create_time_series_chart_option(title: str, series_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Creates a minimal ECharts time-series chart option with only essential data."""
    series_list = series_list if series_list is not None else []
    
    for s in series_list:
        s["type"] = "line"
        
    return {
        "xAxis": {"type": 'time'},
        "series": series_list
    }


# --- End ECharts Option Helpers --- 