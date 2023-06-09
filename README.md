# ERCOT Actual Load by Weather Zone Scrape
Electric Reliability Council of Texas (ERCOT) releases previous day actual load by weather zone every day at 5:50 AM CST. This lambda function scrapes the ERCOT website for the latest actual load file and saves it to an S3 bucket in parquet format. The lambda function is triggered by a CloudWatch event at 13:00 UTC daily.

### Getting Started
Simply adjust the s3_path variable in main.py to point to your S3 folder.

### Deploying
This project has been set up to be deployed as a serverless application via SAM. To deploy the application, run the following command (AWS account and AWS SAM CLI required):
```
sam build
sam deploy --guided
```

### License
This project is licensed under the MIT License