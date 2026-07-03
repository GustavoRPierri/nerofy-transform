resource "aws_glue_catalog_database" "transform" {
  name        = var.glue_database
  description = "Database do Glue Catalog para tabelas geradas pela Lambda nerofy-transform"

  tags = {
    Name        = var.glue_database
    Environment = var.environment
    Service     = "nerofy-transform"
  }
}
