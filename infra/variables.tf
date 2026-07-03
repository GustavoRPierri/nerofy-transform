variable "aws_region" {
  description = "Regiao AWS"
  default     = "sa-east-1"
}

variable "lambda_function_name" {
  description = "Nome da funcao Lambda"
  default     = "nerofy-transform"
}

variable "s3_bronze_bucket" {
  description = "Nome do bucket S3 da camada bronze (origem)"
  default     = "nerofy-bronze-dev"
}

variable "s3_silver_bucket" {
  description = "Nome do bucket S3 da camada silver (destino)"
  default     = "nerofy-silver-dev"
}

variable "glue_database" {
  description = "Nome do database no Glue Catalog"
  default     = "nerofy"
}

variable "log_level" {
  description = "Nivel de log da Lambda"
  default     = "INFO"
}

variable "environment" {
  description = "Ambiente de deploy (dev, prod)"
  default     = "dev"
}
