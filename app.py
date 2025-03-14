#!/usr/bin/env python3
import os
import aws_cdk as cdk
from ai_agent_pipeline.pipeline_stack import AiAgentPipelineStack

app = cdk.App()
AiAgentPipelineStack(app, "AiAgentPipelineStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=app.node.try_get_context('region') or os.getenv('CDK_DEFAULT_REGION')
    )
)

app.synth()
