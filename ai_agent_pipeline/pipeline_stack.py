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

        # Create VPC
        vpc = ec2.Vpc(
            self, "BatchVPC",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )

        # Create Security Group
        security_group = ec2.SecurityGroup(
            self, "BatchSecurityGroup",
            vpc=vpc,
            description="Security group for Batch compute environment",
            allow_all_outbound=True
        )
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
                "AgentName": "ElectronicsManufacturingExpert",
                "AgentResourceRoleArn": agent_role.role_arn,
                "FoundationModel": "anthropic.claude-3-sonnet-20240229-v1:0",
                "Instruction": """You are an Electronics Manufacturing Expert Agent specializing in electronic component manufacturing, assembly processes, and quality control. 

                        Core Knowledge Areas:

                        1. Manufacturing Processes:
                        - PCB fabrication and assembly techniques
                        - Surface-mount technology (SMT) and through-hole assembly
                        - Soldering standards and best practices
                        - Clean room protocols and requirements
                        - Production line optimization

                        2. Electronic Components:
                        - Component specifications and tolerances
                        - Parts selection and compatibility
                        - Component lifecycle management
                        - Inventory control best practices
                        - Component obsolescence management

                        3. Quality Control:
                        - IPC standards implementation
                        - Testing procedures (ICT, FCT, AOI)
                        - Defect analysis and prevention
                        - Statistical process control (SPC)
                        - Reliability testing methods

                        4. Industry Standards:
                        - IPC standards (IPC-A-610, IPC-J-STD-001)
                        - ISO 9001 requirements
                        - ESD protection protocols
                        - RoHS and REACH compliance
                        - Industry 4.0 implementation

                        Response Guidelines:
                        - Provide specific technical details and parameters when discussing processes
                        - Include relevant industry standards and compliance requirements
                        - Emphasize quality control checkpoints and testing procedures
                        - Consider manufacturability and scalability in recommendations
                        - Reference appropriate safety protocols and environmental compliance

                        When responding to queries:
                        1. First assess the specific manufacturing context
                        2. Consider applicable industry standards
                        3. Provide detailed technical specifications
                        4. Include quality control requirements
                        5. Note any relevant compliance considerations

                        Always maintain focus on:
                        - Manufacturing quality and reliability
                        - Process efficiency and optimization
                        - Industry standard compliance
                        - Safety and environmental regulations
                        - Cost-effective solutions while maintaining quality standards""",
                "Description": "Electronics Manufacturing Expert Agent",
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
        # Create IAM role for Lambda with Bedrock permissions - Leave commented until ready to use
        bedrock_lambda_role = iam.Role(
            self, 'BedrockLambdaRole',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com')
        )

        # Add Bedrock permissions - Leave commented until ready to use
        bedrock_lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                'bedrock:InvokeModel',
                'bedrock:InvokeAgent'  # Add this permission
            ],
            resources=['*']
        ))

        # Basic Lambda CloudWatch permissions - Leave commented until ready to use
        bedrock_lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')
        )

        # Create Lambda function for Bedrock integration - Leave commented until ready to use
        bedrock_lambda = lambda_.Function(
            self, 'BedrockLambdaFunction',
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler='index.handler',
            code=lambda_.Code.from_asset('lambda/tools'),
            timeout=Duration.minutes(5),
            memory_size=256,
            role=bedrock_lambda_role,
            environment={
                'POWERTOOLS_SERVICE_NAME': 'bedrock-api',
                'LOG_LEVEL': 'INFO',
                'BEDROCK_AGENT_ID': bedrock_agent_functional.ref,
                'BEDROCK_AGENT_ALIAS_ID': Token.as_string(bedrock_agent_functional_alias.get_att("AgentAliasId"))
            }
        )
        # Create API Gateway REST API - Leave commented until ready to use
        api = aws_apigateway.RestApi(
            self, 'BedrockApi',
            rest_api_name='Bedrock Integration API',
            description='API Gateway integration with Amazon Bedrock'
        )

        # Create API Gateway integration with Lambda - Leave commented until ready to use
        integration = aws_apigateway.LambdaIntegration(
            bedrock_lambda,
            proxy=True,
            integration_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                }
            }]
        )

        # Add POST method to API Gateway - Leave commented until ready to use
        api_resource = api.root.add_resource('invoke')
        api_resource.add_method(
            'POST',
            integration,
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': True
                }
            }]
        )

        # Enable CORS - Leave commented until ready to use
        api_resource.add_cors_preflight(
            allow_origins=['*'],
            allow_methods=['POST'],
            allow_headers=['Content-Type', 'Authorization']
        )

        # Output the API endpoint URL - Leave commented until ready to use
        CfnOutput(
            self, 'ApiEndpoint',
            value=f'{api.url}invoke',
            description='API Gateway endpoint URL'
        )

        # Create IAM roles
        batch_service_role = iam.Role(
            self, "BatchServiceRole",
            assumed_by=iam.ServicePrincipal("batch.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSBatchServiceRole")
            ]
        )

        # Create instance profile for EC2 instances
        batch_instance_role = iam.Role(
            self, "BatchInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2ContainerServiceforEC2Role")
            ]
        )
        # Add this after creating the other IAM roles
        spot_fleet_role = iam.Role(
            self, "SpotFleetRole",
            assumed_by=iam.ServicePrincipal("spotfleet.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2SpotFleetTaggingRole")
            ]
        )


        batch_instance_profile = iam.CfnInstanceProfile(
            self, "BatchInstanceProfile",
            roles=[batch_instance_role.role_name]
        )

        # Your existing repository creation
        repository = codecommit.Repository(
            self, "AiAgentRepo",
            repository_name="ai-agent-repository",
            description="Repository for AI Agent code"
        )

        # Your existing S3 bucket creation
        buildspec_bucket = s3.Bucket(
            self, "BuildspecBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            enforce_ssl=True
        )

        # Copy the asset to the buildspec bucket
        deployment = s3deploy.BucketDeployment(self, "DeployFiles",
            sources=[s3deploy.Source.asset(f"{__dirname}/../ai_agent_pipeline/assets/")],
            destination_bucket=buildspec_bucket
        )

        # Your existing build project
        build_project = codebuild.Project(
            self, "BuildProject",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0
            ),
            source=codebuild.Source.s3(
                bucket=buildspec_bucket,
                path=""
            ),
            environment_variables={
                "TEST_BUCKET": codebuild.BuildEnvironmentVariable(
                    value=buildspec_bucket.bucket_name
                )
            }
        )

        buildspec_bucket.grant_read(build_project)
        buildspec_bucket.grant_read(build_project)
        # Grant Bedrock permissions
        build_project.role.add_to_policy(iam.PolicyStatement(
            actions=["bedrock:*"],
            resources=["*"]
        ))

        # Create Batch compute environment with the new resources
        compute_environment = batch.CfnComputeEnvironment(
            self, "BatchCompute",
            type="MANAGED",
            compute_resources={
                "type": "SPOT",
                "maxvCpus": 16,
                "minvCpus": 0,
                "subnets": [subnet.subnet_id for subnet in vpc.private_subnets],
                "securityGroupIds": [security_group.security_group_id],
                "instanceTypes": ["optimal"],
                "instanceRole": batch_instance_profile.attr_arn,
                "spotIamFleetRole": spot_fleet_role.role_arn,  # Add this line
                "bidPercentage": 60  # Optional: maximum percentage of On-Demand price to bid
            },
            service_role=batch_service_role.role_arn,
            state="ENABLED"
        )

        # Create Batch job queue
        job_queue = batch.CfnJobQueue(
            self, "BatchQueue",
            compute_environment_order=[{
                "computeEnvironment": compute_environment.attr_compute_environment_arn,
                "order": 1
            }],
            priority=1,
            state="ENABLED"
        )

        # Your existing pipeline creation
        pipeline = codepipeline.Pipeline(
            self, "AiAgentPipeline",
            pipeline_name="ai-agent-pipeline"
        )

        source_output = codepipeline.Artifact()
        build_output = codepipeline.Artifact()

        # Add source stage
        pipeline.add_stage(
            stage_name="Source",
            actions=[
                codepipeline_actions.CodeCommitSourceAction(
                    action_name="CodeCommit_Source",
                    repository=repository,
                    output=source_output,
                    branch="main"
                )
            ]
        )

        # Add build stage
        pipeline.add_stage(
            stage_name="Build",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="Build",
                    project=build_project,
                    input=source_output,
                    outputs=[build_output]
                )
            ]
        )

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
        q_business_plugin = CfnResource(
         self, "QBusinessPlugin",
         type="AWS::QBusiness::Plugin",
         properties={
             "ApplicationId": app_id,
             "DisplayName" : "my-new-plugin",
             "Type" : "CUSTOM",
             "AuthConfiguration" : {
                 "NoAuthConfiguration": {}
             },
             "CustomPluginConfiguration" : {
                 "ApiSchema" : {
                     
                     "Payload" : """{
                         "openapi": "3.0.0",
                         "info": {
                             "title": "Bedrock Integration API",
                             "description": "API Gateway integration with Amazon Bedrock",
                             "version": "1.0.0"
                         },
                         "servers": [
                             {
                                 "url": "https://r6arsdd1fh.execute-api.us-west-2.amazonaws.com/prod"
                             }
                         ],
                         "paths": {
                             "/invoke": {
                                 "post": {
                                     "summary": "Invoke Bedrock Agent",
                                     "description": "Sends a prompt to the Bedrock agent and returns the agent's response",
                                     "operationId": "invokeAgent",
                                     "requestBody": {
                                         "required": true,
                                         "content": {
                                             "application/json": {
                                                 "schema": {
                                                     "$ref": "#/components/schemas/InvokeRequest"
                                                 }
                                             }
                                         }
                                     },
                                     "responses": {
                                         "200": {
                                             "description": "Successful response from the agent",
                                             "content": {
                                                 "application/json": {
                                                     "schema": {
                                                         "$ref": "#/components/schemas/InvokeResponse"
                                                     }
                                                 }
                                             }
                                         },
                                         "400": {
                                             "description": "Bad request - missing prompt",
                                             "content": {
                                                 "application/json": {
                                                     "schema": {
                                                         "$ref": "#/components/schemas/ErrorResponse"
                                                     }
                                                 }
                                             }
                                         },
                                         "500": {
                                             "description": "Internal server error",
                                             "content": {
                                                 "application/json": {
                                                     "schema": {
                                                         "$ref": "#/components/schemas/ErrorResponse"
                                                     }
                                                 }
                                             }
                                         }
                                     }
                                 }
                             }
                         },
                         "components": {
                             "schemas": {
                                 "InvokeRequest": {
                                     "type": "object",
                                     "properties": {
                                         "prompt": {
                                             "type": "string",
                                             "description": "The input text to send to the Bedrock agent"
                                         },
                                         "sessionId": {
                                             "type": "string",
                                             "description": "Optional session ID for the conversation (UUID will be generated if not provided)"
                                         }
                                     },
                                     "required": ["prompt"]
                                 },
                                 "InvokeResponse": {
                                     "type": "object",
                                     "properties": {
                                         "agentId": {
                                             "type": "string",
                                             "description": "The ID of the Bedrock agent that processed the request"
                                         },
                                         "response": {
                                             "type": "string",
                                             "description": "The agent's response to the prompt"
                                         },
                                         "sessionId": {
                                             "type": "string",
                                             "description": "The session ID for the conversation"
                                         }
                                     },
                                     "required": ["agentId", "response", "sessionId"]
                                 },
                                 "ErrorResponse": {
                                     "type": "object",
                                     "properties": {
                                         "error": {
                                             "type": "string",
                                             "description": "Error message describing what went wrong"
                                         }
                                     },
                                     "required": ["error"]
                                 }
                             }
                         }
                         }"""
                 },
                 "ApiSchemaType" : "OPEN_API_V3",
                 "Description" : "plugin description"
             },
         }
     )
