import { Role, PolicyStatement, Effect, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

export function createBedrockAgentCoreRole(scope: Construct): Role {
  const role = new Role(scope, 'BedrockAgentCoreRole', {
    roleName: 'bedrock-agent-core-role',
    assumedBy: new ServicePrincipal('bedrock-agentcore.amazonaws.com'),
    description: 'Role for Bedrock Agent Core operations including create_agent_runtime',
  });

  // Add Bedrock Agent Core permissions for create_agent_runtime and related operations
  role.addToPolicy(new PolicyStatement({
    effect: Effect.ALLOW,
    actions: [
      'bedrock-agentcore:CreateAgentRuntime',
      'bedrock-agentcore:GetAgentRuntime',
      'bedrock-agentcore:UpdateAgentRuntime',
      'bedrock-agentcore:DeleteAgentRuntime',
      'bedrock-agentcore:ListAgentRuntimes',
      'bedrock-agentcore:InvokeAgentRuntime'
    ],
    resources: ['*']
  }));

  // Add Bedrock permissions for model invocation
  role.addToPolicy(new PolicyStatement({
    effect: Effect.ALLOW,
    actions: [
      'bedrock:InvokeModel',
      'bedrock:InvokeModelWithResponseStream',
      'bedrock:GetFoundationModel',
      'bedrock:ListFoundationModels'
    ],
    resources: ['*']
  }));

  // Add ECR permissions for Docker image access
  role.addToPolicy(new PolicyStatement({
    effect: Effect.ALLOW,
    actions: [
      'ecr:GetAuthorizationToken',
      'ecr:BatchCheckLayerAvailability',
      'ecr:GetDownloadUrlForLayer',
      'ecr:BatchGetImage'
    ],
    resources: ['*']
  }));

  // Add CloudWatch Logs permissions
  role.addToPolicy(new PolicyStatement({
    effect: Effect.ALLOW,
    actions: [
      'logs:CreateLogGroup',
      'logs:CreateLogStream',
      'logs:PutLogEvents'
    ],
    resources: ['arn:aws:logs:*:*:*']
  }));

  // Add S3 permissions for session storage
  const sessionBucketName = process.env.AGENT_SESSION_S3 || 'agent-sessions-bucket-fallback';
  role.addToPolicy(new PolicyStatement({
    effect: Effect.ALLOW,
    actions: [
      's3:GetObject',
      's3:PutObject',
      's3:DeleteObject',
      's3:ListBucket'
    ],
    resources: [
      `arn:aws:s3:::${sessionBucketName}`,
      `arn:aws:s3:::${sessionBucketName}/*`
    ]
  }));

  // Add S3 permissions for NFL data access
  role.addToPolicy(new PolicyStatement({
    effect: Effect.ALLOW,
    actions: [
      's3:GetObject',
      's3:ListBucket'
    ],
    resources: [
      'arn:aws:s3:::alt-nfl-bucket',
      'arn:aws:s3:::alt-nfl-bucket/*'
    ]
  }));

  // Add Bedrock Knowledge Base permissions
  role.addToPolicy(new PolicyStatement({
    effect: Effect.ALLOW,
    actions: [
      'bedrock:Retrieve',
      'bedrock:RetrieveAndGenerate',
      'bedrock:GetKnowledgeBase',
      'bedrock:ListKnowledgeBases',
      'bedrock:QueryKnowledgeBase'
    ],
    resources: ['*']
  }));

  // Add IAM permissions to pass roles if needed
  role.addToPolicy(new PolicyStatement({
    effect: Effect.ALLOW,
    actions: [
      'iam:PassRole'
    ],
    resources: [
      `arn:aws:iam::*:role/bedrock-*`,
      `arn:aws:iam::*:role/AmazonBedrock*`
    ]
  }));

  return role;
}
