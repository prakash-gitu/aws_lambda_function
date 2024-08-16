import boto3
from datetime import datetime, timedelta

def lambda_handler(event, context):
    # Replace 'your_rds_instance_identifier' with your actual RDS instance identifier
    rds_instance_identifier = 'database-1'
    log_types = ['error/mysql-error-running.log']
    
    # Replace 'your_s3_bucket_name' with the actual name of your S3 bucket
    s3_bucket_name = 'dbbucket111'
    
    rds_client = boto3.client('rds')
    s3_client = boto3.client('s3')
    
    # Get the date for the previous day
    previous_day = datetime.now() - timedelta(days=1)
    previous_day_str = previous_day.strftime('%Y-%m-%d')
    
    for log_type in log_types:
        response = rds_client.describe_db_log_files(
            DBInstanceIdentifier=rds_instance_identifier,
            FilenameContains=log_type
        )
        
        if 'DescribeDBLogFiles' in response:
            for log_file in response['DescribeDBLogFiles']:
                log_file_name = log_file['LogFileName']
                
                # Check if the log file is from the previous day
                if previous_day_str in log_file_name:
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
                    
