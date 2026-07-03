data "aws_s3_bucket" "bronze" {
  bucket = var.s3_bronze_bucket
}

resource "aws_lambda_layer_version" "deps" {
  filename            = "../lambda_layer.zip"
  source_code_hash    = filebase64sha256("../lambda_layer.zip")
  layer_name          = "${var.lambda_function_name}-deps"
  compatible_runtimes = ["python3.12"]
  description         = "Dependencias da Lambda: pydantic, pyarrow, etc."
}

resource "aws_lambda_function" "transform" {
  function_name = var.lambda_function_name
  role          = aws_iam_role.lambda_exec.arn
  handler       = "lambda_handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 120
  memory_size   = 512

  filename         = "../lambda_function.zip"
  source_code_hash = filebase64sha256("../lambda_function.zip")

  layers = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      APP_AWS_REGION    = var.aws_region
      S3_BRONZE_BUCKET  = var.s3_bronze_bucket
      S3_SILVER_BUCKET  = var.s3_silver_bucket
      GLUE_DATABASE     = var.glue_database
      LOG_LEVEL         = var.log_level
      ENV               = var.environment
    }
  }

  tags = {
    Name        = var.lambda_function_name
    Environment = var.environment
    Service     = "nerofy-transform"
  }
}

# Trigger S3: notificar quando um JSON for criado na bronze
resource "aws_s3_bucket_notification" "bronze_notification" {
  bucket = data.aws_s3_bucket.bronze.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.transform.arn
    events              = ["s3:ObjectCreated:Put"]
    filter_prefix       = "bronze/"
    filter_suffix       = ".json"
  }
}

resource "aws_lambda_permission" "allow_bronze_bucket" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.transform.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = data.aws_s3_bucket.bronze.arn
}
