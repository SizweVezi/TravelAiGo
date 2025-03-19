terraform {
  required_version = ">= 1.0.0" # Ensure that the Terraform version is 1.0.0 or higher

  required_providers {
    aws = {
      source = "hashicorp/aws" # Specify the source of the AWS provider
      version = "~> 4.0"        # Use a version of the AWS provider that is compatible with version
    }
    null = {
      source  = "hashicorp/null"
      version = "3.2.3"
    }
  }
}

provider "aws" {
  region = "us-east-1" # Set the AWS region to US East (N. Virginia)
  shared_credentials_files = ["~/.aws/credentials"] # Use the credentials file located at ~/.aws/credentials
}

resource "aws_secretsmanager_secret" "amadeus_secret" {
  name = "amadeus_secret"
  description = "amadeus secret key"
}

resource "aws_secretsmanager_secret_version" "amadeus_api_key" {
  secret_id = aws_secretsmanager_secret.amadeus_secret.id
  secret_string = jsonencode({
    "CLIENT_ID"     = "jdGnQ3CHefvnvx9eGWOuR7ECfrZsFQot",
    "CLIENT_SECRET" = "ix412GA6CCjlwGzA"
})
}

resource "aws_iam_role" "zuluchain_lambda_role" {
  name = "terraform_lambda_role" # Set the name of the IAM role to terraform_lambda_role
  assume_role_policy = <<EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }
  EOF
}

# IAM Policy for the Lambda function
resource "aws_iam_policy" "zuluchain_lambda_policy" {
  name        = "terraform_lambda_policy"
  path        = "/"
  description = "IAM policy for the Lambda function"
  policy      = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
EOF
}

# IAM Policy for getting the secret
resource "aws_iam_policy" "get_secret_policy" {
  name        = "terraform_secrets_policy"
  path        = "/"
  description = "IAM policy for getting secrets"
  policy      = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "*"
    }
  ]
}
EOF
}


# Attach the IAM policy to the IAM role
resource "aws_iam_role_policy_attachment" "zuluchain_lambda_policy_attachment" {
  policy_arn = aws_iam_policy.zuluchain_lambda_policy.arn # Use the ARN of the IAM policy
  role = aws_iam_role.zuluchain_lambda_role.name # Attach the IAM policy to the IAM role
}

# Attach the IAM secrets policy to the Lambda IAM role
resource "aws_iam_role_policy_attachment" "secrets_policy_attachment" {
  policy_arn = aws_iam_policy.get_secret_policy.arn
  role       = aws_iam_role.zuluchain_lambda_role.name
}

# Code archive for the Hotel search Lambda function
# data "archive_file" "zip_hotel_search_engine" {
#     type        = "zip"
#     source_dir  = "${path.module}/package_hotel"
#     output_path = "${path.module}/hotel_search_engine.zip"
#     excludes    = ["__pycache__", "*.pyc"]
#     depends_on  = [null_resource.hotel_install_dependencies]
# }

# resource "null_resource" "hotel_install_dependencies" {
#   triggers = {
#     dependencies_versions = filemd5("${path.module}/../src/requirements.txt")
#     source_versions = filemd5("${path.module}/../src/hotel_search_engine.py")
#   }
#
#    provisioner "local-exec" {
#         command = "bash ${path.module}/package.sh"
#    }
#}


# hotel search engine Lambda function
# resource "aws_lambda_function" "terraform_lambda_func" {
#     filename         = data.archive_file.zip_hotel_search_engine.output_path
#     source_code_hash = data.archive_file.zip_hotel_search_engine.output_base64sha256
#     function_name    = "hotel_search_engine_function"
#     role            = aws_iam_role.zuluchain_lambda_role.arn
#     handler         = "hotel_search_engine.lambda_handler"
#     runtime         = "python3.9"
#     timeout         = 30
#     memory_size     = 256
#     environment {
#         variables = {
#             CLIENT_ID     = "jdGnQ3CHefvnvx9eGWOuR7ECfrZsFQot"
#             CLIENT_SECRET = "ix412GA6CCjlwGzA"
#         }
#     }
#     depends_on      = [aws_iam_policy_attachment.zuluchain_lambda_policy_attachment]
# }

#=======================================================================================================================

#Flight configuration

#Zip the flight search engine code
data "archive_file" "zip_flight_search_engine" {
    type        = "zip"
    source_dir = "${path.module}/package_flight"
    output_path = "${path.module}/flight_search_engine.zip"
#    excludes    = ["__pycache__", "*.pyc"]
    depends_on  = [null_resource.flight_install_dependencies]
}
#Create a dependency to files for the lambda function
resource "null_resource" "flight_install_dependencies" {
    triggers = {
        dependencies_versions = filemd5("${path.module}/../src/requirements.txt")
        source_versions = filemd5("${path.module}/../src/flight_search_engine.py")
    }

    provisioner "local-exec" {
        command = "bash ${path.module}/package.sh"
    }
}

# Flight search engine Lambda function
resource "aws_lambda_function" "terraform_lambda_func_flight" {
    filename         = data.archive_file.zip_flight_search_engine.output_path
    source_code_hash = data.archive_file.zip_flight_search_engine.output_base64sha256
    function_name    = "flight_search_engine_function"
    role            = aws_iam_role.zuluchain_lambda_role.arn
    handler         = "flight_search_engine.lambda_handler"
    runtime         = "python3.9"
    timeout         = 30
    memory_size     = 256
     depends_on      = [aws_iam_role_policy_attachment.zuluchain_lambda_policy_attachment]
}

# Output the ARN of the Lambda function
output "lambda_function_arn" {
  value = aws_lambda_function.terraform_lambda_func_flight.arn
}

output "terraform_lambda_role_arn" {
  value = aws_iam_role.zuluchain_lambda_role.arn
}

output "terraform_logging_arn_output" {
  value = "aws_iam_policy.iam_for_lambda.arn"
}