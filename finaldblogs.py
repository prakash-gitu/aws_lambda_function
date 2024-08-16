import boto3
import os
from datetime import datetime, timedelta, timezone

def lambda_handler(event, context):
    # Get environment variables
    rds_instance_identifier = os.environ['RDS_INSTANCE_IDENTIFIER']
    s3_bucket_name = os.environ['S3_BUCKET_NAME']
    
    log_types = ['error/mysql-error-running.log', 'slowquery/mysql-slowquery.log']
    
    rds_client = boto3.client('rds')
    s3_client = boto3.client('s3')
    
    # Get the cutoff time of 24hrs ago
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
    previous_day_str = cutoff_time.strftime('%Y-%m-%d')
    
    for log_type in log_types:
        response = rds_client.describe_db_log_files(
            DBInstanceIdentifier=rds_instance_identifier,
            FilenameContains=log_type
        )
        
        if 'DescribeDBLogFiles' in response:
            for log_file in response['DescribeDBLogFiles']:
                log_file_name = log_file['LogFileName']
                
                # Get the last written timestamp of the log file
                last_written = datetime.utcfromtimestamp(log_file['LastWritten'] / 1000).replace(tzinfo=timezone.utc)
                
                # Check if the log file was last written within the last 24 hours
                if last_written >= cutoff_time:
                    log_file_data = ''
                    
                    marker = '0'
                    while True:
                        log_file_data_response = rds_client.download_db_log_file_portion(
                            DBInstanceIdentifier=rds_instance_identifier,
                            LogFileName=log_file_name,
                            Marker=marker
                        )
                        log_file_data += log_file_data_response['LogFileData']
                        
                        if not log_file_data_response['AdditionalDataPending']:
                            break
                        else:
                            marker = log_file_data_response['Marker']
                    
                    # Upload the log data to S3
                    s3_key = f'{previous_day_str}/{log_file_name}'
                    s3_client.put_object(Bucket=s3_bucket_name, Key=s3_key, Body=log_file_data)
