from constructs import Construct
import os

from aws_cdk import (
    Stack,
    aws_codecommit as codecommit,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codebuild as codebuild,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_batch as batch,
    aws_cloudwatch as cloudwatch,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_s3_deployment as s3deploy,
    aws_apigateway as aws_apigateway,
    Duration,
    RemovalPolicy,
    CfnResource,
    CfnParameter,
    CfnOutput,
    Token,
    Fn
)

class AiAgentPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        #parameters - For an extra challenge set up the ApplicationId as a parameter
        # identity_center_arn = CfnParameter(
        #     self, "IdentityCenterArn",
        #     type="String",
        #     description="The ARN of the IAM Identity Center instance",
        #     default="",  # Empty string as default value
        #     allowed_pattern="^$|^arn:[\\w-]+:sso:::instance/(sso)?ins-[a-zA-Z0-9-.]{16}$",  # Allows empty string or valid IAM Identity Center ARN
        #     constraint_description="Must be a valid IAM Identity Center instance ARN or empty string"
        # )

        # app_id = Fn.import_value("QBusinessApp") - Uncomment for an extra challenge
        app_id = "<your Q App Id>"

        __dirname = os.path.dirname(os.path.realpath(__file__))

        #Create bedrock agents for testing
        # Create IAM role for the agents
        agent_role = iam.Role(
            self, "BedrockAgentRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="IAM role for Bedrock agents"
        )

        # Add required policies to the role
        agent_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
        )

        # Create the first agent using CfnAgent
        bedrock_agent_test = CfnResource(
            self, "TestAgent",
            type="AWS::Bedrock::Agent",
            properties={
                "AgentName": "ContentCreatorAgent",
                "AgentResourceRoleArn": agent_role.role_arn,
                "FoundationModel": "anthropic.claude-3-sonnet-20240229-v1:0",
                "Instruction": "You are an agent that tests other Bedrock agents for Quality Assurance.",
                "Description": "Agent specialized in content creation",
                "IdleSessionTTLInSeconds": 1800
            }
        )

        bedrock_agent_functional = CfnResource(
            self, "FunctionalAgent",
            type="AWS::Bedrock::Agent",
            properties={
                "AgentName": "GeneralQuestionsExpert",
                "AgentResourceRoleArn": agent_role.role_arn,
                "FoundationModel": "anthropic.claude-3-sonnet-20240229-v1:0",
                "Instruction": """You are a bedrock agent that answers general questions""",
                "Description": "General Question Agent",
                "IdleSessionTTLInSeconds": 1800
            }
        )
        bedrock_agent_functional_alias = CfnResource(
            self, "FunctionalAgentAlias",
            type="AWS::Bedrock::AgentAlias",
            properties={
                "AgentId": bedrock_agent_functional.ref,
                "AgentAliasName": "latest"
            }
        )

        # Output the agent IDs
        CfnOutput(self, "FirstAgentId", value=bedrock_agent_test.ref)
        CfnOutput(self, "FunctionalAgentId", value=bedrock_agent_functional.ref)

        #Create Lambda Function to Integrate with API Gateway
        #@# Create IAM role for Lambda with Bedrock permissions
        #@bedrock_lambda_role = iam.Role(
        #@     self, 'BedrockLambdaRole',
        #@     assumed_by=iam.ServicePrincipal('lambda.amazonaws.com')
        #@)

        #@# Add Bedrock permissions
        #@bedrock_lambda_role.add_to_policy(iam.PolicyStatement(
        #@     effect=iam.Effect.ALLOW,
        #@     actions=[
        #@         'bedrock:InvokeModel',
        #@         'bedrock:InvokeAgent'  # Add this permission
        #@     ],
        #@     resources=['*']
        #@))

        #@# Basic Lambda CloudWatch permissions
        #@bedrock_lambda_role.add_managed_policy(
        #@     iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')
        #@)

        #@# Create Lambda function for Bedrock integration
        #@bedrock_lambda = lambda_.Function(
        #@     self, 'BedrockLambdaFunction',
        #@     runtime=lambda_.Runtime.PYTHON_3_9,
        #@     handler='index.handler',
        #@     code=lambda_.Code.from_asset('lambda/tools'),
        #@     timeout=Duration.minutes(5),
        #@     memory_size=256,
        #@     role=bedrock_lambda_role,
        #@     environment={
        #@         'POWERTOOLS_SERVICE_NAME': 'bedrock-api',
        #@         'LOG_LEVEL': 'INFO',
        #@         'BEDROCK_AGENT_ID': bedrock_agent_functional.ref,
        #@         'BEDROCK_AGENT_ALIAS_ID': Token.as_string(bedrock_agent_functional_alias.get_att("AgentAliasId"))
        #@     }
        #@)
        #@# Create API Gateway REST API
        #@api = aws_apigateway.RestApi(
        #@     self, 'BedrockApi',
        #@     rest_api_name='Bedrock Integration API',
        #@     description='API Gateway integration with Amazon Bedrock'
        #@ )

        #@# Create API Gateway integration with Lambda
        #@integration = aws_apigateway.LambdaIntegration(
        #@     bedrock_lambda,
        #@     proxy=True,
        #@     integration_responses=[{
        #@         'statusCode': '200',
        #@         'responseParameters': {
        #@             'method.response.header.Access-Control-Allow-Origin': "'*'"
        #@         }
        #@     }]
        #@)

        #@# Add POST method to API Gateway
        #@ api_resource = api.root.add_resource('invoke')
        #@api_resource.add_method(
        #@     'POST',
        #@     integration,
        #@     method_responses=[{
        #@         'statusCode': '200',
        #@         'responseParameters': {
        #@             'method.response.header.Access-Control-Allow-Origin': True
        #@         }
        #@     }]
        #@)

        #@# Enable CORS
        #@api_resource.add_cors_preflight(
        #@     allow_origins=['*'],
        #@     allow_methods=['POST'],
        #@     allow_headers=['Content-Type', 'Authorization']
        #@)

        #@# Output the API endpoint URL
        #@CfnOutput(
        #@     self, 'ApiEndpoint',
        #@     value=f'{api.url}invoke',
        #@     description='API Gateway endpoint URL'
        #@)


        # Your existing Lambda function
        tools_function = lambda_.Function(
            self, "ToolsFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_asset("lambda/tools"),
            timeout=Duration.minutes(5)
        )

        # Your existing CloudWatch dashboard
        dashboard = cloudwatch.Dashboard(
            self, "AiAgentDashboard",
            dashboard_name="ai-agent-metrics"
        )

        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Agent Invocations",
                left=[
                    tools_function.metric_invocations(),
                    tools_function.metric_errors()
                ]
            ),
            cloudwatch.GraphWidget(
                title="Agent Latency",
                left=[tools_function.metric_duration()]
            )
        )
