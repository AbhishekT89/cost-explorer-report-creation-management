import json
import boto3
import pandas as pd
from io import StringIO

ce_client = boto3.client('ce')
s3 = boto3.client('s3')
bucket_name="cost-explorer-graghical-data-generation"

def creating_csv_from_data(report_data,csv_name):
    
    data = []
    for result in report_data['ResultsByTime']:
        time_period = result['TimePeriod']
        usage_amount = result['Total']['UnblendedCost']['Amount']
        
        data.append({
            'TimePeriod.Start': time_period['Start'],
            'TimePeriod.End': time_period['End'],
            'usage_Amount': usage_amount,
        })
        
    json_data = str(data).replace('\n', '').replace(' ', '').replace("'",'"')
    df = pd.json_normalize(json.loads(json_data))
    csv_buffer = StringIO()
    csv_file_path = 'reports/output.csv'
    df.to_csv(csv_buffer, index=False)
    s3.put_object(Body=csv_buffer.getvalue(), Bucket=bucket_name, Key=csv_file_path)
    print(f'CSV file "{csv_file_path}" created successfully.')
    



def lambda_handler(event, context):
    print(event)
    
    ######### Financial: Annual  #############
    
    annual_response = ce_client.get_cost_and_usage(
    TimePeriod={
        'Start': '2023-01-01',
        'End': '2023-12-31'
    },
    Granularity='MONTHLY',
    Metrics=[
        'UnblendedCost',
    ])
    
    print(annual_response)
    creating_csv_from_data(annual_response,"annual_data.csv")
    
    ######### Financial: Top Services ##########
    
    top_services_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': '2023-01-01',
            'End': '2023-12-31'
        },
        Granularity='MONTHLY',
        Filter={
            'Not':{'Dimensions':{
                    'Key': 'RECORD_TYPE',
                    'Values': [
                        'Credit',
                ]}
        }},
        GroupBy=[
        {
            'Type': 'DIMENSION',
            'Key': 'SERVICE'
        }
    ],Metrics=[
        'UnblendedCost',
    ]
    )
    print("Financial: Top Services",top_services_response)
    
    
    # ###########  Financial: Spend As Compared to Last Month ##########
    
    last_month_spend_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': '2023-12-01',
            'End': '2023-12-31'
        },
        Granularity='MONTHLY',
        GroupBy=[
        {
            'Type': 'DIMENSION',
            'Key': 'SERVICE'
        },
    ],Metrics=[
        'UnblendedCost',
    ])
    print("Financial: Spend As Compared to Last Month",last_month_spend_response)
    
    ######### Financial: Charge Type ###################
    
    charge_type_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': '2023-01-01',
            'End': '2023-12-31'
        },
        Granularity='MONTHLY',
        GroupBy=[
        {
            'Type': 'DIMENSION',
            'Key': 'RECORD_TYPE'
        },
    ],Metrics=[
        'UnblendedCost',
    ])
    print("Financail: Charge Type",charge_type_response)
    
    ######### Financial:  API Operation ###################
    
    api_operation_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': '2023-01-01',
            'End': '2023-12-31'
        },
        Granularity='MONTHLY',
        GroupBy=[
        {
            'Type': 'DIMENSION',
            'Key': 'OPERATION'
        },
    ],Metrics=[
        'UnblendedCost',
    ])
    print("Financail: API Operation",api_operation_response)
    
    
    ######### Financial: Usage ###################
    
    usage_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': '2023-01-01',
            'End': '2023-12-31'
        },
        Granularity='MONTHLY',
        GroupBy=[
        {
            'Type': 'DIMENSION',
            'Key': 'USAGE_TYPE'
        },
    ],Metrics=[
        'UnblendedCost',
    ])
    print("Financail: API Operation",usage_response)
    
    ######### Financial: S3 Spends ###################
    
    s3_spends_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': '2023-01-01',
            'End': '2023-12-31'
        },
        Granularity='MONTHLY',
        Filter={
            'Dimensions':{
                'Key': 'USAGE_TYPE_GROUP',
                'Values': [
                    'S3',
            ]}
        },
    Metrics=[
        'UnblendedCost',
    ])
    print("Financail: S3 Spends",s3_spends_response)
    
    ######### Financial: EBS Spends ###################
    
    ebs_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': '2023-01-01',
            'End': '2023-12-31'
        },
        Granularity='MONTHLY',
        Filter={
            'Dimensions':{
                'Key': 'USAGE_TYPE_GROUP',
                'Values': [
                    'EC2:EBS-SSD(gp2)',
                    'EC2:EBS-SSD(gp3)'
            ]}
        },
    Metrics=[
        'UnblendedCost',
    ])
    print("Financail: EBS",ebs_response)
    
    
    ######### Financial: Regions ###################
    
    regions_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': '2023-01-01',
            'End': '2023-12-31'
        },
        Granularity='MONTHLY',
        GroupBy=[
        {
            'Type': 'DIMENSION',
            'Key': 'REGION'
        }],
    Metrics=[
        'UnblendedCost',
    ])
    print("Financail: Regions",regions_response)
    
    ######### Financial: AZ ###################
    
    az_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': '2023-01-01',
            'End': '2023-12-31'
        },
        Granularity='MONTHLY',
        GroupBy=[
        {
            'Type': 'DIMENSION',
            'Key': 'AZ'
        }],
    Metrics=[
        'UnblendedCost',
    ])
    print("Financail: AZ",az_response)
    
    ######### Financial: DB Engine ###################
    
    db_engine_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': '2023-01-01',
            'End': '2023-12-31'
        },
        Granularity='MONTHLY',
        GroupBy=[
        {
            'Type': 'DIMENSION',
            'Key': 'DATABASE_ENGINE'
        }],
        Filter={
            'Dimensions':{
                'Key': 'DATABASE_ENGINE',
                'Values': [
                    'Amazon DocumentDB',
                    'MySQL',
                    'PostgreSQL'
            ]}
        },
    Metrics=[
        'UnblendedCost',
    ])
    print("Financail: DB Engine",db_engine_response)
    
    
    ######### Financial: Platform ###################
    
    platform_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': '2023-01-01',
            'End': '2023-12-31'
        },
        Granularity='MONTHLY',
        GroupBy=[
        {
            'Type': 'DIMENSION',
            'Key': 'PLATFORM'
        }],
    Metrics=[
        'UnblendedCost',
    ])
    print("Financail: Platform",platform_response)
    
    ######### Financial: Snapshot and Backup ###################
    
    snapshot_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': '2023-01-01',
            'End': '2023-12-31'
        },
        Granularity='MONTHLY',
        GroupBy=[
        {
            'Type': 'DIMENSION',
            'Key': 'USAGE_TYPE'
        }],
        Filter={
            'Dimensions':{
                'Key': 'USAGE_TYPE',
                'Values': [
                    'APS3-EBS:SnapshotUsage (GB-Month)',
            ]}
        },
    Metrics=[
        'UnblendedCost',
    ])
    print("Financail: Snapshot",snapshot_response)
    
    
    ######### Financial: Snapshot and Backup ###################
    
    snapshot_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': '2023-01-01',
            'End': '2023-12-31'
        },
        Granularity='MONTHLY',
        GroupBy=[
        {
            'Type': 'DIMENSION',
            'Key': 'USAGE_TYPE'
        }],
        Filter={
            'Dimensions':{
                'Key': 'USAGE_TYPE',
                'Values': [
                    'APS3-EBS:SnapshotUsage (GB-Month)',
            ]}
        },
    Metrics=[
        'UnblendedCost',
    ])
    print("Financail: Snapshot",snapshot_response)
    
    ######### Financial: Purchase Option and RI Usage ###################
    
    purchase_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': '2023-01-01',
            'End': '2023-12-31'
        },
        Granularity='MONTHLY',
        GroupBy=[
        {
            'Type': 'DIMENSION',
            'Key': 'PURCHASE_TYPE'
        }],
    Metrics=[
        'UnblendedCost',
    ])
    print("Financail: Purchase Option and RI Usage",purchase_response)
    
    
    
    
    
