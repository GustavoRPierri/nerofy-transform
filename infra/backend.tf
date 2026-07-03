terraform {
  backend "s3" {
    bucket         = "nerofy-terraform-state"
    key            = "nerofy-transform/terraform.tfstate"
    region         = "sa-east-1"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}
