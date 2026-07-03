resource "aws_s3_bucket" "silver" {
  bucket = var.s3_silver_bucket
  force_destroy = false

  tags = {
    Name        = var.s3_silver_bucket
    Environment = var.environment
    Service     = "nerofy-transform"
  }
}

resource "aws_s3_bucket_versioning" "silver" {
  bucket = aws_s3_bucket.silver.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "silver" {
  bucket = aws_s3_bucket.silver.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
