variable "aws_region" {
  default = "sa-east-1"
}

variable "github_repo" {
  description = "Repositório GitHub no formato owner/repo"
  default     = "GustavoRPierri/nerofy-transform"
}

# ── OIDC Provider ────────────────────────────────────────────────────────────

data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

# ── Role: deploy em produção (main) ──────────────────────────────────────────

resource "aws_iam_role" "github_deploy" {
  name = "github-actions-deploy-nerofy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = data.aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          "token.actions.githubusercontent.com:sub" = [
            "repo:${var.github_repo}:ref:refs/heads/main",
            "repo:${var.github_repo}:ref:refs/heads/release/*",
            "repo:${var.github_repo}:ref:refs/heads/hotfix/*"
          ]
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "github_deploy" {
  name = "github-actions-deploy-nerofy-policy"
  role = aws_iam_role.github_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TerraformState"
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
        Resource = [
          "arn:aws:s3:::nerofy-terraform-state",
          "arn:aws:s3:::nerofy-terraform-state/*"
        ]
      },
      {
        Sid    = "Lambda"
        Effect = "Allow"
        Action = [
          "lambda:CreateFunction", "lambda:UpdateFunctionCode",
          "lambda:UpdateFunctionConfiguration", "lambda:Get*",
          "lambda:List*", "lambda:DeleteFunction",
          "lambda:AddPermission", "lambda:RemovePermission",
          "lambda:PublishLayerVersion", "lambda:DeleteLayerVersion",
          "lambda:InvokeFunction", "lambda:TagResource", "lambda:UntagResource"
        ]
        Resource = "*"
      },
      {
        Sid    = "IAM"
        Effect = "Allow"
        Action = [
          "iam:CreateRole", "iam:UpdateRole", "iam:DeleteRole",
          "iam:Get*", "iam:List*", "iam:PassRole",
          "iam:AttachRolePolicy", "iam:DetachRolePolicy",
          "iam:PutRolePolicy", "iam:DeleteRolePolicy",
          "iam:TagRole", "iam:UntagRole"
        ]
        Resource = [
          "arn:aws:iam::*:role/nerofy-*",
          "arn:aws:iam::*:role/github-actions-*"
        ]
      },
      {
        Sid    = "S3"
        Effect = "Allow"
        Action = [
          "s3:CreateBucket", "s3:DeleteBucket",
          "s3:Get*", "s3:List*", "s3:Put*",
          "s3:PutBucketNotification", "s3:PutBucketVersioning",
          "s3:PutEncryptionConfiguration",
          "s3:PutBucketPublicAccessBlock",
          "s3:PutBucketOwnershipControls",
          "s3:TagResource"
        ]
        Resource = [
          "arn:aws:s3:::nerofy-bronze-*",
          "arn:aws:s3:::nerofy-bronze-*/*",
          "arn:aws:s3:::nerofy-silver-*",
          "arn:aws:s3:::nerofy-silver-*/*"
        ]
      },
      {
        Sid    = "Glue"
        Effect = "Allow"
        Action = [
          "glue:GetDatabase", "glue:GetTable",
          "glue:CreateTable", "glue:UpdateTable"
        ]
        Resource = [
          "arn:aws:glue:${var.aws_region}:*:catalog",
          "arn:aws:glue:${var.aws_region}:*:database/*",
          "arn:aws:glue:${var.aws_region}:*:table/*",
        ]
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup", "logs:DeleteLogGroup",
          "logs:DescribeLogGroups", "logs:TagResource"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/nerofy-*"
      }
    ]
  })
}

# ── Role: CI / testes (release/*, hotfix/*) ────────────────────────────────

resource "aws_iam_role" "github_ci" {
  name = "github-actions-ci-nerofy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = data.aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          "token.actions.githubusercontent.com:sub" = [
            "repo:${var.github_repo}:ref:refs/heads/release/*",
            "repo:${var.github_repo}:ref:refs/heads/hotfix/*"
          ]
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "github_ci" {
  name = "github-actions-ci-nerofy-policy"
  role = aws_iam_role.github_ci.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "LambdaInvoke"
        Effect = "Allow"
        Action = [
          "lambda:GetFunction", "lambda:GetFunctionConfiguration",
          "lambda:InvokeFunction", "lambda:ListFunctions"
        ]
        Resource = "*"
      },
      {
        Sid    = "S3ReadWrite"
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
        Resource = [
          "arn:aws:s3:::nerofy-bronze-*",
          "arn:aws:s3:::nerofy-bronze-*/*",
          "arn:aws:s3:::nerofy-silver-*",
          "arn:aws:s3:::nerofy-silver-*/*"
        ]
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:FilterLogEvents", "logs:DescribeLogStreams",
          "logs:GetLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/nerofy-*"
      }
    ]
  })
}

# ── Outputs ──────────────────────────────────────────────────────────────────

output "github_deploy_role_arn" {
  description = "ARN da role OIDC para deploy — usar como AWS_ROLE_ARN_DEPLOY no GitHub"
  value       = aws_iam_role.github_deploy.arn
}

output "github_ci_role_arn" {
  description = "ARN da role OIDC para CI — usar como AWS_ROLE_ARN_CI no GitHub"
  value       = aws_iam_role.github_ci.arn
}
