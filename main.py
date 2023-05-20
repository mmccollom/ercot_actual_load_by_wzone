from datetime import datetime, timedelta
from ercotutils import misutil
import io
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytz


def execute():
    report_type_id = '13101'
    s3_path = 's3://ercot-62841215/actual_load_by_weather_zone/'

    # create cut_off_dt from publish_date and publish_hour
    local_tz = pytz.timezone('America/Chicago')
    cut_off_dt = datetime.now(local_tz) - timedelta(hours=datetime.now(local_tz).hour,
                                                    minutes=datetime.now(local_tz).minute,
                                                    seconds=datetime.now(local_tz).second)

    print(f'Cutoff Date: {cut_off_dt}')

    # get document list from ERCOT
    documents_dict = misutil.get_ice_doc_list(report_type_id)

    # load documents into dataframe
    df = pd.json_normalize(documents_dict)
    df['Document.PublishDate'] = pd.to_datetime(df['Document.PublishDate'], format='%Y-%m-%dT%H:%M:%S%z')

    # create a new column for y/m/d as a str of publish date
    df['Document.PublishDateStr'] = df['Document.PublishDate'].dt.strftime('%Y-%m-%d')

    # create a new column for the Hour of publish date
    df['Document.PublishHour'] = df['Document.PublishDate'].dt.hour

    # filter dataframe to remove files published prior to cut_off_dt
    df = df[(df['Document.PublishDate'] > cut_off_dt) & (df['Document.FriendlyName'].str.endswith('csv'))]
    # export dataframe to json
    documents_dict = json.loads(df.to_json(orient='records'))

    # assert documents_dict is not None and size is 1
    assert documents_dict is not None and len(documents_dict) == 1, f'No documents found for report_type_id: {report_type_id}'

    for document in documents_dict:
        document_id = document['Document.DocID']
        document_content = misutil.get_zipped_file_contents(document_id).decode('utf-8')

        # read document_content into buffer
        document_content = io.StringIO(document_content)

        # read bytes into dataframe
        df = pd.read_csv(document_content)

        # trim extra whitespace from column names
        df.columns = df.columns.str.strip()

        # rename columns
        col_remap = {'OperDay': 'delivery_date', 'HourEnding': 'hour_ending', 'COAST': 'coast', 'EAST': 'east',
                     'FAR_WEST': 'far_west', 'NORTH': 'north', 'NORTH_C': 'north_c', 'SOUTHERN': 'southern',
                     'SOUTH_C': 'south_c', 'WEST': 'west', 'DSTFlag': 'is_day_light_savings', 'TOTAL': 'system_total'}
        df.rename(columns=col_remap, inplace=True)

        # convert delivery_date to datetime 05/18/2023
        df['delivery_date'] = pd.to_datetime(df['delivery_date'], format='%m/%d/%Y')

        # reformat delivery_date str in format YYYY-MM-DD
        df['delivery_date'] = df['delivery_date'].dt.strftime('%Y-%m-%d')

        # trim :00 from hour_ending
        df['hour_ending'] = df['hour_ending'].str.replace(':00', '')

        # change hour_ending to integer
        df['hour_ending'] = df['hour_ending'].astype(int)

        print(df.columns)
        # write dataframe to s3 using pyarrow
        table = pa.Table.from_pandas(df=df)
        pq.write_to_dataset(table=table, root_path=s3_path, compression='snappy',
                            partition_cols=['delivery_date'])


def lambda_handler(event, context):
    print("In Lambda Handler")
    execute()


if __name__ == "__main__":
    print("In Main")
    execute()
