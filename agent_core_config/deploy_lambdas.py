#!/usr/bin/env python3
import boto3
import json
import zipfile
import io
import os
import time

def get_nfl_data_bucket():
    """Get the NFL data bucket name"""
    return "alt-nfl-bucket"

def create_lambda_zip_from_directory(directory_path):
    """Create a zip file from a directory containing handler.py and requirements.txt"""
    import subprocess
    import tempfile
    import shutil
    
    zip_buffer = io.BytesIO()
    
    # Create temporary directory for building the package
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy handler.py
        handler_path = os.path.join(directory_path, 'handler.py')
        if os.path.exists(handler_path):
            shutil.copy2(handler_path, temp_dir)
        else:
            raise FileNotFoundError(f"handler.py not found in {directory_path}")
        
        # Install dependencies if requirements.txt exists
        requirements_path = os.path.join(directory_path, 'requirements.txt')
        if os.path.exists(requirements_path):
            print(f"Installing dependencies from {requirements_path}...")
            try:
                # Try using uv pip install
                subprocess.run([
                    'uv', 'pip', 'install', '-r', requirements_path, '--target', temp_dir
                ], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    # Fallback to system pip
                    subprocess.run([
                        'python3', '-m', 'pip', 'install', '-r', requirements_path, '-t', temp_dir
                    ], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Warning: Could not install dependencies: {e}")
                    print("Lambda may fail if dependencies are required")
        
        # Create zip file from temp directory
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arc_name)
    
    zip_buffer.seek(0)
    return zip_buffer.read()

def create_or_update_lambda(lambda_client, function_name, zip_content, handler, description, environment_vars=None):
    """Create or update a Lambda function"""
    
    # Check if function exists
    try:
        lambda_client.get_function(FunctionName=function_name)
        function_exists = True
        print(f"📝 Function {function_name} exists, updating...")
    except lambda_client.exceptions.ResourceNotFoundException:
        function_exists = False
        print(f"🆕 Creating new function {function_name}...")
    
    if function_exists:
        # Update existing function
        try:
            # Update function code
            lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            
            # Update function configuration if environment variables provided
            if environment_vars:
                lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    Environment={'Variables': environment_vars}
                )
            
            print(f"✅ Updated function {function_name}")
            
        except Exception as e:
            print(f"❌ Error updating function {function_name}: {e}")
            return None
    else:
        # Create new function
        try:
            # Get or create execution role
            role_arn = get_or_create_lambda_role()
            
            create_params = {
                'FunctionName': function_name,
                'Runtime': 'python3.11',
                'Role': role_arn,
                'Handler': handler,
                'Code': {'ZipFile': zip_content},
                'Description': description,
                'Timeout': 120,
                'MemorySize': 512,
                'Publish': True
            }
            
            if environment_vars:
                create_params['Environment'] = {'Variables': environment_vars}
            
            response = lambda_client.create_function(**create_params)
            print(f"✅ Created function {function_name}")
            
            # Wait for function to be active
            waiter = lambda_client.get_waiter('function_active')
            waiter.wait(FunctionName=function_name)
            
        except Exception as e:
            print(f"❌ Error creating function {function_name}: {e}")
            return None
    
    # Get function info
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        return response['Configuration']
    except Exception as e:
        print(f"❌ Error getting function info for {function_name}: {e}")
        return None

def get_or_create_lambda_role():
    """Get or create IAM role for Lambda functions"""
    iam_client = boto3.client('iam')
    role_name = 'nfl-mcp-lambda-role'
    
    try:
        # Try to get existing role
        response = iam_client.get_role(RoleName=role_name)
        print(f"📋 Using existing role: {role_name}")
        return response['Role']['Arn']
    except iam_client.exceptions.NoSuchEntityException:
        print(f"🆕 Creating new role: {role_name}")
        
        # Create role
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for NFL MCP Lambda functions'
        )
        
        role_arn = response['Role']['Arn']
        
        # Attach basic Lambda execution policy
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        
        # Create and attach custom policy for NFL data access
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        "arn:aws:s3:::alt-nfl-bucket",
                        "arn:aws:s3:::alt-nfl-bucket/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "athena:StartQueryExecution",
                        "athena:GetQueryExecution",
                        "athena:GetQueryResults",
                        "athena:StopQueryExecution"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock-agent-runtime:Retrieve"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "glue:GetDatabase",
                        "glue:GetTable",
                        "glue:GetPartitions"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        policy_name = f"{role_name}-policy"
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document)
        )
        
        print(f"✅ Created role with policies: {role_name}")
        
        # Wait a bit for role to propagate
        time.sleep(10)
        
        return role_arn

def main():
    """Deploy all NFL MCP Lambda functions"""
    print("🚀 Starting NFL MCP Lambda deployment...")
    
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Initialize AWS clients
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Get NFL data bucket
    nfl_bucket = get_nfl_data_bucket()
    print(f"📦 Using NFL data bucket: {nfl_bucket}")
    
    # Lambda functions to deploy
    functions = [
        {
            'name': 'nfl-data-service',
            'directory': os.path.join(current_dir, 'nfl-data-service'),
            'handler': 'handler.lambda_handler',
            'description': 'NFL MCP service for Athena database queries',
            'environment': {}
        },
        {
            'name': 'nfl-game-service',
            'directory': os.path.join(current_dir, 'nfl-game-service'),
            'handler': 'handler.lambda_handler',
            'description': 'NFL MCP service for game data retrieval',
            'environment': {}
        },
        {
            'name': 'nfl-knowledge-service',
            'directory': os.path.join(current_dir, 'nfl-knowledge-service'),
            'handler': 'handler.lambda_handler',
            'description': 'NFL MCP service for knowledge base search',
            'environment': {
                'KNOWLEDGE_BASE_ID': 'ZJOYGGYSJM'  # NFL Knowledge Base ID
            }
        }
    ]
    
    deployed_functions = []
    
    for func_config in functions:
        print(f"\n📦 Processing {func_config['name']}...")
        
        try:
            # Create zip file
            zip_content = create_lambda_zip_from_directory(func_config['directory'])
            
            # Deploy function
            function_info = create_or_update_lambda(
                lambda_client=lambda_client,
                function_name=func_config['name'],
                zip_content=zip_content,
                handler=func_config['handler'],
                description=func_config['description'],
                environment_vars=func_config['environment'] if func_config['environment'] else None
            )
            
            if function_info:
                deployed_functions.append({
                    'name': func_config['name'],
                    'arn': function_info['FunctionArn'],
                    'version': function_info['Version']
                })
                print(f"✅ Successfully deployed {func_config['name']}")
            else:
                print(f"❌ Failed to deploy {func_config['name']}")
                
        except Exception as e:
            print(f"❌ Error processing {func_config['name']}: {e}")
    
    print(f"\n🎉 Deployment complete! Deployed {len(deployed_functions)} functions:")
    for func in deployed_functions:
        print(f"  📋 {func['name']}: {func['arn']}")
    
    print(f"\n📝 Next steps:")
    print(f"  1. Update KNOWLEDGE_BASE_ID in nfl-knowledge-service if needed")
    print(f"  2. Run gateway_deploy.py to create the MCP Gateway")
    print(f"  3. Test with test_mcp_gateway.py")

if __name__ == "__main__":
    main()
