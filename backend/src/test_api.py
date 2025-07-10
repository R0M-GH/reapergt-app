import json

def get_cors_headers():
    """Get CORS headers for all responses."""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
    }

def lambda_handler(event, context):
    """Simple test handler to verify basic Lambda functionality."""
    try:
        print(f"Received event: {json.dumps(event)}")
        
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        
        # Handle CORS preflight
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'CORS preflight OK'})
            }
        
        # Simple test response
        if path == '/crns':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'crns': [],
                    'message': 'Test API working - authentication disabled',
                    'user': 'test-user'
                })
            }
        
        # Default response
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'Test API working',
                'method': http_method,
                'path': path
            })
        }
        
    except Exception as e:
        print(f"Error in test handler: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Test handler error: {str(e)}'})
        } 