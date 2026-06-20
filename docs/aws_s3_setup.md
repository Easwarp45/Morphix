# Cloud File Converter — AWS S3 + CloudFront Setup Guide

This guide walks you through configuring AWS S3 for file storage and CloudFront as a CDN for production.

---

## Part 1: Create S3 Bucket

### 1.1 Create Bucket

```bash
aws s3api create-bucket \
  --bucket cloud-file-converter-prod \
  --region us-east-1
```

For regions other than `us-east-1`:
```bash
aws s3api create-bucket \
  --bucket cloud-file-converter-prod \
  --region ap-south-1 \
  --create-bucket-configuration LocationConstraint=ap-south-1
```

### 1.2 Block Public Access

```bash
aws s3api put-public-access-block \
  --bucket cloud-file-converter-prod \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### 1.3 Enable Versioning (Optional — for file recovery)

```bash
aws s3api put-bucket-versioning \
  --bucket cloud-file-converter-prod \
  --versioning-configuration Status=Enabled
```

### 1.4 Configure Lifecycle Policy (Auto-delete expired files)

Create `lifecycle.json`:
```json
{
  "Rules": [
    {
      "ID": "DeleteExpiredConversions",
      "Status": "Enabled",
      "Filter": { "Prefix": "conversions/" },
      "Expiration": { "Days": 7 }
    },
    {
      "ID": "DeleteExpiredUploads",
      "Status": "Enabled",
      "Filter": { "Prefix": "uploads/" },
      "Expiration": { "Days": 3 }
    },
    {
      "ID": "DeleteAbortedMultipartUploads",
      "Status": "Enabled",
      "Filter": { "Prefix": "" },
      "AbortIncompleteMultipartUpload": { "DaysAfterInitiation": 1 }
    }
  ]
}
```

Apply:
```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket cloud-file-converter-prod \
  --lifecycle-configuration file://lifecycle.json
```

### 1.5 Enable Server-Side Encryption

```bash
aws s3api put-bucket-encryption \
  --bucket cloud-file-converter-prod \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      },
      "BucketKeyEnabled": true
    }]
  }'
```

---

## Part 2: Create IAM User for the Application

### 2.1 Create IAM Policy

Create `s3_policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::cloud-file-converter-prod",
        "arn:aws:s3:::cloud-file-converter-prod/*"
      ]
    }
  ]
}
```

```bash
aws iam create-policy \
  --policy-name CloudFileConverterS3Policy \
  --policy-document file://s3_policy.json
```

### 2.2 Create IAM User

```bash
aws iam create-user --user-name cloudfileconverter-app

aws iam attach-user-policy \
  --user-name cloudfileconverter-app \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/CloudFileConverterS3Policy

aws iam create-access-key --user-name cloudfileconverter-app
```

Save the `AccessKeyId` and `SecretAccessKey` to your `.env.production`.

---

## Part 3: CloudFront CDN

### 3.1 Create Origin Access Control (OAC)

```bash
aws cloudfront create-origin-access-control \
  --origin-access-control-config '{
    "Name": "CloudFileConverterOAC",
    "Description": "OAC for Cloud File Converter S3",
    "SigningProtocol": "sigv4",
    "SigningBehavior": "always",
    "OriginAccessControlOriginType": "s3"
  }'
```

Note the returned `Id`.

### 3.2 Create CloudFront Distribution

```bash
aws cloudfront create-distribution \
  --distribution-config '{
    "CallerReference": "cloudfileconverter-'$(date +%s)'",
    "DefaultCacheBehavior": {
      "ViewerProtocolPolicy": "redirect-to-https",
      "AllowedMethods": {
        "Quantity": 7,
        "Items": ["GET","HEAD","OPTIONS","PUT","POST","PATCH","DELETE"],
        "CachedMethods": {"Quantity": 2, "Items": ["GET","HEAD"]}
      },
      "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
      "TargetOriginId": "S3-cloud-file-converter-prod",
      "ForwardedValues": {
        "QueryString": false,
        "Cookies": {"Forward": "none"}
      },
      "MinTTL": 0
    },
    "Origins": {
      "Quantity": 1,
      "Items": [{
        "Id": "S3-cloud-file-converter-prod",
        "DomainName": "cloud-file-converter-prod.s3.amazonaws.com",
        "S3OriginConfig": {"OriginAccessIdentity": ""},
        "OriginAccessControlId": "YOUR_OAC_ID"
      }]
    },
    "Enabled": true,
    "Comment": "Cloud File Converter CDN",
    "PriceClass": "PriceClass_100",
    "ViewerCertificate": {
      "CloudFrontDefaultCertificate": true
    }
  }'
```

### 3.3 Update S3 Bucket Policy for CloudFront

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "cloudfront.amazonaws.com"
    },
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::cloud-file-converter-prod/*",
    "Condition": {
      "StringEquals": {
        "AWS:SourceArn": "arn:aws:cloudfront::YOUR_ACCOUNT_ID:distribution/YOUR_DISTRIBUTION_ID"
      }
    }
  }]
}
```

```bash
aws s3api put-bucket-policy \
  --bucket cloud-file-converter-prod \
  --policy file://cloudfront_bucket_policy.json
```

### 3.4 Set `AWS_S3_CUSTOM_DOMAIN`

After CloudFront is created, note the distribution domain (e.g., `dXXXXXXXXXXXX.cloudfront.net`) and set:

```env
AWS_S3_CUSTOM_DOMAIN=dXXXXXXXXXXXX.cloudfront.net
```

---

## Part 4: CORS Configuration for S3

Required for browser-direct uploads:

```bash
aws s3api put-bucket-cors \
  --bucket cloud-file-converter-prod \
  --cors-configuration '{
    "CORSRules": [{
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedOrigins": [
        "https://cloudfileconverter.com",
        "https://www.cloudfileconverter.com",
        "https://cloudfileconverter.vercel.app"
      ],
      "ExposeHeaders": ["ETag"],
      "MaxAgeSeconds": 3600
    }]
  }'
```

---

## Part 5: Verification

```bash
# Verify bucket exists and is encrypted
aws s3api get-bucket-encryption --bucket cloud-file-converter-prod

# Verify public access is blocked
aws s3api get-public-access-block --bucket cloud-file-converter-prod

# Test upload
aws s3 cp test.txt s3://cloud-file-converter-prod/test/test.txt
aws s3 ls s3://cloud-file-converter-prod/test/
aws s3 rm s3://cloud-file-converter-prod/test/test.txt

# Test CloudFront URL
curl -I https://dXXXXXXXXXXXX.cloudfront.net/uploads/test.txt
```

---

## Cost Estimation (Monthly)

| Service | Usage | Estimated Cost |
|---------|-------|---------------|
| S3 Storage | 10 GB | ~$0.23 |
| S3 Requests | 100K | ~$0.04 |
| CloudFront Transfer | 50 GB | ~$4.25 |
| CloudFront Requests | 1M | ~$0.75 |
| **Total** | | **~$5.27/mo** |
