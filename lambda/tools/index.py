import json
import boto3
import os
import uuid

def handler(event, context):
    """
    Lambda function handling Bedrock Agent requests through API Gateway.
    Processes incoming requests and invokes a Bedrock agent.
    """
    try:
        # Initialize Bedrock Agent Runtime client
        bedrock_agent = boto3.client('bedrock-agent-runtime')
        
        # Extract request body
        body = json.loads(event.get('body', '{}'))
        
        # Get the input text/prompt
        input_text = body.get('prompt')
        
        if not input_text:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'Prompt is required'
                })
            }

        # Get agent ID from environment variable
        agent_id = os.environ.get('BEDROCK_AGENT_ID')
        agent_alias_id = os.environ.get('BEDROCK_AGENT_ALIAS_ID')
        
        if not agent_id or not agent_alias_id:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'Agent ID or Agent Alias ID not configured'
                })
            }

        # Invoke Bedrock agent
        response = bedrock_agent.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=body.get('sessionId', str(uuid.uuid4())),  # This is correct
            inputText=input_text
        )
        # Extract completion from the event stream
        completion = ""
        for event in response['completion']:
            chunk = event['chunk']
            if 'bytes' in chunk:
                completion += chunk['bytes'].decode('utf-8')
        # Parse and return response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'agentId': agent_id,
                'response': completion,
                'sessionId': response.get('sessionId')
            })
        }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }