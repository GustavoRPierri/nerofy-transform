output "lambda_function_name" {
  value = aws_lambda_function.transform.function_name
}

output "lambda_role_arn" {
  value = aws_iam_role.lambda_exec.arn
}

output "s3_silver_bucket" {
  value = aws_s3_bucket.silver.id
}

output "s3_bronze_bucket" {
  value = data.aws_s3_bucket.bronze.id
}

output "glue_database" {
  value = var.glue_database
}
