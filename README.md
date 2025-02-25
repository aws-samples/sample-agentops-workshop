# AI Agent Pipeline for AWS Bedrock and Amazon Q Integration

This project implements an AI agent pipeline using AWS CDK, integrating AWS Bedrock agents and Amazon Q Business applications. It provides a robust infrastructure for deploying and managing AI-powered tools and services.

The AI Agent Pipeline is designed to streamline the process of creating, deploying, and managing AI agents within an AWS environment. It leverages various AWS services to create a scalable and flexible architecture for AI-driven applications.

Key features of this pipeline include:
- Integration with AWS Bedrock for AI agent creation and management
- Utilization of Amazon Q Business for advanced querying and data retrieval
- Automated deployment process using AWS CDK
- Secure networking setup with VPC and associated resources
- Scalable compute resources using AWS Batch

## Repository Structure

```
.
├── ai_agent_pipeline
│   ├── __init__.py
│   └── pipeline_stack.py
├── app.py
├── buildspec.yml
├── cdk.context.json
├── cdk.json
├── lambda
│   └── tools
│       └── index.py
├── README.md
└── requirements.txt
```

Key Files:
- `app.py`: The entry point for the CDK application
- `ai_agent_pipeline/pipeline_stack.py`: Defines the main infrastructure stack
- `lambda/tools/index.py`: Lambda function code for AI agent tools
- `buildspec.yml`: AWS CodeBuild specification file
- `requirements.txt`: Python dependencies for the project

## Usage Instructions

### Installation

Prerequisites:
- Python 3.9 or later
- AWS CLI configured with appropriate credentials
- AWS CDK v2.0.0 or later

To set up the project:

1. Clone the repository:
   ```
   git clone <repository-url>
   cd ai-agent-pipeline
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

### Deployment

To deploy the AI Agent Pipeline:

1. Synthesize the CloudFormation template:
   ```
   cdk synth
   ```

2. Deploy the stack:
   ```
   cdk deploy
   ```

3. Follow the prompts to confirm the deployment.

### Configuration

The `cdk.json` file contains the configuration for the CDK application. You can modify this file to adjust the deployment settings.

Key configuration options:
- `app`: Specifies the entry point for the CDK application (default: "python3 app.py")
- `watch`: Defines which files to watch for changes during development

### Testing & Quality

To run the tests:

```
python -m pytest tests/
```

The `buildspec.yml` file defines the CI/CD process, including running tests and uploading test reports to an S3 bucket.

### Troubleshooting

Common issues and solutions:

1. CDK Synthesis Fails
   - Problem: The `cdk synth` command fails with an error.
   - Solution: 
     1. Ensure all dependencies are installed: `pip install -r requirements.txt`
     2. Check for any syntax errors in the Python files
     3. Verify that your AWS credentials are correctly configured

2. Deployment Fails
   - Problem: The `cdk deploy` command fails to create resources.
   - Solution:
     1. Check the CloudFormation console for detailed error messages
     2. Ensure your AWS account has the necessary permissions to create the resources
     3. Verify that you're not exceeding any AWS service limits

3. Lambda Function Errors
   - Problem: The Lambda function is not executing correctly.
   - Solution:
     1. Check the CloudWatch Logs for the Lambda function
     2. Ensure the function has the correct permissions
     3. Verify that the function code is correctly packaged and deployed

For more detailed debugging:

1. Enable verbose logging in CDK:
   ```
   cdk --debug deploy
   ```

2. Check CloudWatch Logs for detailed Lambda function logs.

3. Use the AWS CloudFormation console to inspect the stack and its resources.

## Data Flow

The AI Agent Pipeline processes requests and data through the following flow:

1. User or system initiates a request to the AI agent.
2. The request is routed through API Gateway to the appropriate Lambda function.
3. The Lambda function processes the request and interacts with the Bedrock agent or Amazon Q Business application as needed.
4. If required, the Lambda function queries the data source (S3 bucket) for additional information.
5. The Bedrock agent or Amazon Q Business application processes the request using the provided data and AI models.
6. The response is sent back through the Lambda function and API Gateway to the user.

```
[User/System] -> [API Gateway] -> [Lambda Function] -> [Bedrock Agent/Amazon Q]
                                        |
                                        v
                                  [S3 Data Source]
```

Important technical considerations:
- Ensure proper IAM roles and permissions are set up for each component.
- Monitor Lambda function performance and adjust resource allocations as needed.
- Regularly update and maintain the data in the S3 bucket for accurate AI responses.

## Infrastructure

The AI Agent Pipeline infrastructure is defined using AWS CDK and includes the following key resources:

VPC:
- VPC (BatchVPC): A VPC with CIDR block 10.0.0.0/16
- Public Subnets: Two public subnets in different availability zones
- Private Subnets: Two private subnets in different availability zones
- Internet Gateway: For public internet access
- NAT Gateways: For outbound internet access from private subnets

Security:
- Security Group (BatchSecurityGroup): For controlling network access to Batch resources

IAM Roles:
- BedrockAgentRole: IAM role for Bedrock agents with AmazonBedrockFullAccess
- QBusinessServiceRole: IAM role for Amazon Q Business with S3 access permissions
- BatchServiceRole: IAM role for AWS Batch service
- BatchInstanceRole: IAM role for EC2 instances in Batch compute environments
- SpotFleetRole: IAM role for Spot Fleet requests

AI and Data Resources:
- Bedrock Agents: Two Bedrock agents (TestAgent and FunctionalAgent) for different purposes
- Amazon Q Business Application (AIAgent): Main Q Business application
- Amazon Q Business Index (AIAgentIndex): Index for the Q Business application
- Amazon Q Business Retriever (AIAgentRetriever): Retriever for the Q Business application
- S3 Bucket (DataSourceBucket): Bucket for storing data used by the AI agents
- Amazon Q Business Data Source (AIAgentDataSource): Connects the S3 bucket to the Q Business application
- Amazon Q Business Plugin (AIAgentPlugin): Defines the API schema for the Q Business application

CodeCommit:
- Repository (AiAgentRepo): CodeCommit repository for storing the project code

The infrastructure is designed to be scalable and secure, with separate public and private subnets, and appropriate IAM roles for each component. The AI resources are integrated with the necessary data sources and configured for optimal performance.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

