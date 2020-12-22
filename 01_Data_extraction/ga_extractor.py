from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json

def initialize_analyticsreporting(KEY_FILE_LOCATION, SCOPES):
    """Initializes an Analytics Reporting API V4 service object.
    Returns: An authorized Analytics Reporting API V4 service object."""

    credentials = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE_LOCATION, SCOPES)

    # Build the service object.
    analytics = build('analyticsreporting', 'v4', credentials=credentials)

    return analytics


def get_report(analytics, metrics, dimensions, start, end, VIEW_ID):
    """Queries the Analytics Reporting API V4.
    Args:
    analytics: An authorized Analytics Reporting API V4 service object.
    Returns:
    The Analytics Reporting API V4 response.
    Using date range 2020-11-09 to 2020-11-15 for testing purposes"""
    METS = [f'ga:{metric}' for metric in metrics]
    DIMS = [f'ga:{dimension}' for dimension in dimensions]
    
    return analytics.reports().batchGet(
        body={
            'reportRequests': [
                                {
                                    'viewId': VIEW_ID,
                                    'dateRanges': [{'startDate': start,
                                                    'endDate': end}],
                                    'metrics': [{'expression': expression} for expression in METS],
                                    'orderBys': [{'fieldName': METS[0], 
                                                  'sortOrder': 'DESCENDING'}],
                                    'dimensions': [{'name': name} for name in DIMS]
                                }]
            }).execute(), METS, DIMS


def to_df(response, METS, DIMS):
    data_dict = {f"{i}": [] for i in DIMS + METS}
    
    for report in response.get('reports', []):
        rows = report.get('data', {}).get('rows', [])
        for row in rows:
            for i, key in enumerate(DIMS):
                data_dict[key].append(row.get('dimensions', [])[i])
            date_values = row.get('metrics', [])
            for values in date_values:
                all_values = values.get('values', [])
                for i, key in enumerate(METS):
                    data_dict[key].append(all_values[i])
                    
    df = pd.DataFrame(data=data_dict)
    df.columns = [col.split(':')[-1] for col in df.columns]
    
    return df


def ga_to_df(metrics,dimensions,start,end,KEY_FILE_LOCATION,SCOPES,VIEW_ID):
    '''metrics = list, dimesnions = list,
    start = str, end = str'''
    analytics = initialize_analyticsreporting(KEY_FILE_LOCATION,SCOPES)
    response, METS, DIMS = get_report(analytics,metrics,dimensions,start,end,VIEW_ID)
    response_df = to_df(response, metrics, dimensions)
    
    return response_df