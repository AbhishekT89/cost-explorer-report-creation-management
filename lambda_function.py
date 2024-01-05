import json
import boto3
import pandas as pd
from io import StringIO
import yaml

ce_client = boto3.client('ce')
s3 = boto3.client('s3')
bucket_name="cost-explorer-graghical-data-generation"


def generic_report_creation(dict_response, reportName):
    print(reportName)
    print(dict_response)
    var_list = []
    for i in dict_response:
        print(i)

        if "ResultsByTime" == i:
            for j in dict_response[i]:
                start = j["TimePeriod"]["Start"]
                end = j["TimePeriod"]["End"]
                total = j["Total"]
                            
                if  reportName=="annual":
                    Amount = total["UnblendedCost"]["Amount"]
                    Unit = total["UnblendedCost"]["Unit"]

                    var_list.append(
                        {
                            "Start": start,
                            "End": end,
                            "Amount": float(Amount),
                            "USD": Unit,
                        }
                    )
                    
                if "Groups" in j:
                    for k in j["Groups"]:
                        if (
                            reportName == "top_services"
                            or reportName == "last_month_spend"
                            or reportName == "charge_type"
                            or reportName == "usage"
                            or reportName == "linked_account"
                            or reportName == "db_engine"
                            or reportName == "platform"
                            or reportName == "snapshot"
                            or reportName == "purchase"
                        ):
                            serviceName = k["Keys"][0]
                            Amount = k["Metrics"]["UnblendedCost"]["Amount"]
                            Unit = k["Metrics"]["UnblendedCost"]["Unit"]

                            var_list.append(
                                {
                                    "Start": start,
                                    "End": end,
                                    "ServiceName": serviceName,
                                    "Amount": float(Amount),
                                    "USD": Unit,
                                }
                            )

                        elif reportName == "s3_spends":
                            serviceName = k["Keys"][0]
                            Amount = k["Metrics"]["UnblendedCost"]["Amount"]
                            Unit = k["Metrics"]["UnblendedCost"]["Unit"]
                            s3Amount = k["Metrics"]["UsageQuantity"]["Amount"]
                            s3Unit = k["Metrics"]["UsageQuantity"]["Unit"]
                            var_list.append(
                                {
                                    "Start": start,
                                    "End": end,
                                    "ServiceName": serviceName,
                                    "Amount": float(Amount),
                                    "USD": Unit,
                                    "S3Amount": s3Amount,
                                    "S3Unit": s3Unit,
                                }
                            )

                        elif reportName == "annual":
                            Amount = j["Total"]["UnblendedCost"]["Amount"]
                            Unit = j["Total"]["UnblendedCost"]["Unit"]

                            var_list.append(
                                {
                                    "Start": start,
                                    "End": end,
                                    "Amount": float(Amount),
                                    "USD": Unit,
                                }
                            )

                        elif reportName == "ebs_spends":
                            functionality = k["Keys"][0]
                            ebsAmount = k["Metrics"]["UsageQuantity"]["Amount"]
                            Amount = k["Metrics"]["UnblendedCost"]["Amount"]
                            Unit = k["Metrics"]["UnblendedCost"]["Unit"]
                            ebsUnit = k["Metrics"]["UsageQuantity"]["Unit"]
                            var_list.append(
                                {
                                    "Start": start,
                                    "End": end,
                                    "Functionality": functionality,
                                    "Amount": float(Amount),
                                    "USD": Unit,
                                    "EbsAmount": ebsAmount,
                                    "EbsUnit": ebsUnit,
                                }
                            )

                        elif reportName == "regions":
                            servregionNameiceName = k["Keys"][0]
                            Amount = k["Metrics"]["UnblendedCost"]["Amount"]
                            Unit = k["Metrics"]["UnblendedCost"]["Unit"]

                            var_list.append(
                                {
                                    "Start": start,
                                    "End": end,
                                    "ServiceName": servregionNameiceName,
                                    "Amount": float(Amount),
                                    "USD": Unit,
                                }
                            )

                        elif reportName == "az":
                            availbilityZone = k["Keys"][0]
                            Amount = k["Metrics"]["UnblendedCost"]["Amount"]
                            Unit = k["Metrics"]["UnblendedCost"]["Unit"]

                            var_list.append(
                                {
                                    "Start": start,
                                    "End": end,
                                    "AvailbilityZone": availbilityZone,
                                    "Amount": float(Amount),
                                    "USD": Unit,
                                }
                            )

                        elif reportName == "api_operation":
                            operation = k["Keys"][0]
                            Amount = k["Metrics"]["UnblendedCost"]["Amount"]
                            Unit = k["Metrics"]["UnblendedCost"]["Unit"]

                            var_list.append(
                                {
                                    "Start": start,
                                    "End": end,
                                    "Operation": operation,
                                    "Amount": float(Amount),
                                    "USD": Unit,
                                }
                            )

    df = pd.DataFrame(var_list)
    csv_buffer = StringIO()
    csv_file_path = f'reports/{reportName}.csv'
    df.to_csv(csv_buffer, index=False)
    s3.put_object(Body=csv_buffer.getvalue(), Bucket=bucket_name, Key=csv_file_path)
    print(f'CSV file "{csv_file_path}" created successfully.')
    # df.to_csv(f"{reportName}.csv", encoding="utf-8", index=False)


def run_query(query_name, query_filters):
    # Update time period in filters
    query_filters['query']['TimePeriod']['Start'] = query_filters['query']['TimePeriod']['Start'].strftime('%Y-%m-%d')
    query_filters['query']['TimePeriod']['End'] = query_filters['query']['TimePeriod']['End'].strftime('%Y-%m-%d')

    print(query_filters['query'])
    
    response = ce_client.get_cost_and_usage(**query_filters['query'])
    
    generic_report_creation(response, query_name)
    

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

    ########## Reading Yaml File ########################

    # Load filters from YAML file
    with open('config.yaml', 'r') as yaml_file:
        config = yaml.safe_load(yaml_file)

    # Iterate through each query in the YAML file
    for query_name, query_filters in config['queries'].items():
        run_query(query_name, query_filters)
    
    
    
    # ######## Financial: Annual  #############
    
    # annual_response = ce_client.get_cost_and_usage(
    # TimePeriod={
    #     'Start': '2023-01-01',
    #     'End': '2023-12-31'
    # },
    # Granularity='MONTHLY',
    # Metrics=[
    #     'UnblendedCost',
    # ])
    
    # print(annual_response)
    # creating_csv_from_data(annual_response,"annual_data.csv")
    
    ######## Financial: Top Services ##########
    
    # top_services_response = ce_client.get_cost_and_usage(
    #     TimePeriod={
    #         'Start': '2023-01-01',
    #         'End': '2023-12-31'
    #     },
    #     Granularity='MONTHLY',
    #     Filter={
    #         'Not':{'Dimensions':{
    #                 'Key': 'RECORD_TYPE',
    #                 'Values': [
    #                     'Credit',
    #             ]}
    #     }},
    #     GroupBy=[
    #     {
    #         'Type': 'DIMENSION',
    #         'Key': 'SERVICE'
    #     }
    # ],Metrics=[
    #     'UnblendedCost',
    # ]
    # )
    # print("Financial: Top Services",top_services_response)
    
    
    
    
 
        
        
    
    
    
    # ###########  Financial: Spend As Compared to Last Month ##########
    
    # last_month_spend_response = ce_client.get_cost_and_usage(
    #     TimePeriod={
    #         'Start': '2023-12-01',
    #         'End': '2023-12-31'
    #     },
    #     Granularity='MONTHLY',
    #     GroupBy=[
    #     {
    #         'Type': 'DIMENSION',
    #         'Key': 'SERVICE'
    #     },
    # ],Metrics=[
    #     'UnblendedCost',
    # ])
    # print("Financial: Spend As Compared to Last Month",last_month_spend_response)
    
    # ######### Financial: Charge Type ###################
    
    # charge_type_response = ce_client.get_cost_and_usage(
    #     TimePeriod={
    #         'Start': '2023-01-01',
    #         'End': '2023-12-31'
    #     },
    #     Granularity='MONTHLY',
    #     GroupBy=[
    #     {
    #         'Type': 'DIMENSION',
    #         'Key': 'RECORD_TYPE'
    #     },
    # ],Metrics=[
    #     'UnblendedCost',
    # ])
    # print("Financail: Charge Type",charge_type_response)
    
    # ######### Financial:  API Operation ###################
    
    # api_operation_response = ce_client.get_cost_and_usage(
    #     TimePeriod={
    #         'Start': '2023-12-01',
    #         'End': '2023-12-31'
    #     },
    #     Granularity='MONTHLY',
    #     GroupBy=[
    #     {
    #         'Type': 'DIMENSION',
    #         'Key': 'OPERATION'
    #     },
    # ],Metrics=[
    #     'UnblendedCost',
    # ])
    # print("Financail: API Operation",api_operation_response)
    
    
    # ######### Financial: Usage ###################
    
    # usage_response = ce_client.get_cost_and_usage(
    #     TimePeriod={
    #         'Start': '2023-12-01',
    #         'End': '2023-12-31'
    #     },
    #     Granularity='MONTHLY',
    #     GroupBy=[
    #     {
    #         'Type': 'DIMENSION',
    #         'Key': 'USAGE_TYPE'
    #     },
    # ],Metrics=[
    #     'UnblendedCost',
    # ])
    # print("Financail: Usage ",usage_response)
    
    # ######### Financial: S3 Spends ###################
    
    # s3_spends_response = ce_client.get_cost_and_usage(
    #     TimePeriod={
    #         'Start': '2023-09-01',
    #         'End': '2023-12-31'
    #     },
    #     Granularity='MONTHLY',
    #     GroupBy=[{
    #         'Type': 'DIMENSION',
    #         'Key': 'SERVICE'
    #     }],
    #     Filter={
    #         'Dimensions':{
    #             'Key': 'USAGE_TYPE_GROUP',
    #             'Values': [
    #                 'S3: Storage - Standard',
    #         ]}
    #     },
    #     Metrics=[
    #         'UnblendedCost',
    #         'UsageQuantity'
    #     ])
    # print("Financail: S3 Spends",s3_spends_response)
    
    # ######### Financial: EBS Spends ###################
    
    # ebs_response = ce_client.get_cost_and_usage(
    #     TimePeriod={
    #         'Start': '2023-01-01',
    #         'End': '2023-12-31'
    #     },
    #     Granularity='MONTHLY',
    #     GroupBy=[{
    #         'Type': 'DIMENSION',
    #         'Key': 'USAGE_TYPE'
    #     }],
    #     Filter={
    #         'Dimensions':{
    #             'Key': 'USAGE_TYPE',
    #             'Values': [
    #                 'APS3-EBS:VolumeUsage.gp3',
    #                 'APS3-EBS:VolumeUsage.gp2'
    #         ]}
    #     },
    #     Metrics=[
    #         'UnblendedCost',
    #         'UsageQuantity'
    #     ])
    # print("Financail: EBS",ebs_response)
    
    
    ############## Financial: Linked Accounts ##################
    
    # linked_account_response = ce_client.get_cost_and_usage(
    #     TimePeriod={
    #         'Start': '2023-09-01',
    #         'End': '2023-12-31'
    #     },
    #     Granularity='MONTHLY',
    #     GroupBy=[
    #     {
    #         'Type': 'DIMENSION',
    #         'Key': 'LINKED_ACCOUNT'
    #     }],
    #     Metrics=[
    #         'UnblendedCost',
    # ])
       
    # print("Financail: Linked Accounts",linked_account_response) 
    
    
    # ######### Financial: Regions ###################
    
    # regions_response = ce_client.get_cost_and_usage(
    #     TimePeriod={
    #         'Start': '2023-09-01',
    #         'End': '2023-12-31'
    #     },
    #     Granularity='MONTHLY',
    #     GroupBy=[
    #     {
    #         'Type': 'DIMENSION',
    #         'Key': 'REGION'
    #     }],
    # Metrics=[
    #     'UnblendedCost',
    # ])
    # print("Financail: Regions",regions_response)
    
    # ######### Financial: AZ ###################
    
    # az_response = ce_client.get_cost_and_usage(
    #     TimePeriod={
    #         'Start': '2023-09-01',
    #         'End': '2023-12-31'
    #     },
    #     Granularity='MONTHLY',
    #     GroupBy=[
    #     {
    #         'Type': 'DIMENSION',
    #         'Key': 'AZ'
    #     }],
    # Metrics=[
    #     'UnblendedCost',
    # ])
    # print("Financail: AZ",az_response)
    
    # ######### Financial: DB Engine ###################
    
    # db_engine_response = ce_client.get_cost_and_usage(
    #     TimePeriod={
    #         'Start': '2023-01-01',
    #         'End': '2023-12-31'
    #     },
    #     Granularity='MONTHLY',
    #     GroupBy=[
    #     {
    #         'Type': 'DIMENSION',
    #         'Key': 'DATABASE_ENGINE'
    #     }],
    #     Filter={
    #         'Dimensions':{
    #             'Key': 'DATABASE_ENGINE',
    #             'Values': [
    #                 'Amazon DocumentDB',
    #                 'MySQL',
    #                 'PostgreSQL'
    #         ]}
    #     },
    # Metrics=[
    #     'UnblendedCost',
    # ])
    # print("Financail: DB Engine",db_engine_response)
    
    
    # ######### Financial: Platform ###################
    
    # platform_response = ce_client.get_cost_and_usage(
    #     TimePeriod={
    #         'Start': '2023-09-01',
    #         'End': '2023-12-31'
    #     },
    #     Granularity='MONTHLY',
    #     GroupBy=[
    #     {
    #         'Type': 'DIMENSION',
    #         'Key': 'PLATFORM'
    #     }],
    # Metrics=[
    #     'UnblendedCost',
    # ])
    # print("Financail: Platform",platform_response)
    
    # ######### Financial: Snapshot and Backup ###################
    
    # snapshot_response = ce_client.get_cost_and_usage(
    #     TimePeriod={
    #         'Start': '2023-01-01',
    #         'End': '2023-12-31'
    #     },
    #     Granularity='MONTHLY',
    #     GroupBy=[
    #     {
    #         'Type': 'DIMENSION',
    #         'Key': 'USAGE_TYPE'
    #     }],
    #     Filter={
    #         'Dimensions':{
    #             'Key': 'USAGE_TYPE',
    #             'Values': [
    #                 'APS3-EBS:SnapshotUsage',
    #         ]}
    #     },
    #     Metrics=[
    #         'UnblendedCost',
    #     ])
    # print("Financail: Snapshot",snapshot_response)
    
    
    # ######### Financial: Purchase Option and RI Usage ###################
    
    # purchase_response = ce_client.get_cost_and_usage(
    #     TimePeriod={
    #         'Start': '2023-01-01',
    #         'End': '2023-12-31'
    #     },
    #     Granularity='MONTHLY',
    #     GroupBy=[
    #     {
    #         'Type': 'DIMENSION',
    #         'Key': 'PURCHASE_TYPE'
    #     }],
    # Metrics=[
    #     'UnblendedCost',
    # ])
    # print("Financail: Purchase Option and RI Usage",purchase_response)
    
    
    
    
    
