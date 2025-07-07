# ReaperGT PWA Backend API

This is the backend API for the ReaperGT PWA, built with AWS Lambda, API Gateway, DynamoDB, and Cognito authentication.

## Architecture

- **API Gateway**: RESTful API with JWT authentication
- **Lambda Functions**: Python 3.13 functions for handling API requests
- **DynamoDB**: Two tables for storing user data and CRN information
- **Cognito**: User authentication and JWT token management
- **Secrets Manager**: Secure storage for application secrets

## API Endpoints

All endpoints require authentication via Cognito JWT token in the `Authorization` header.

### GET /crns
List all CRNs tracked by the authenticated user.

**Response:**
```json
{
  "crns": ["12345", "67890"]
}
```

### POST /crns
Add a CRN to the authenticated user's tracked list.

**Request Body:**
```json
{
  "crn": "12345"
}
```

**Response:**
```json
{
  "message": "CRN added successfully",
  "crn": "12345",
  "course_info": {
    "course_id": "CS 1331",
    "course_name": "Introduction to Object-Oriented Programming",
    "course_section": "A"
  }
}
```

**Validation:**
- CRN must be 5 digits
- CRN must exist in OSCAR
- Maximum 5 CRNs per user
- CRN cannot already be in user's list

### DELETE /crns/{crn}
Remove a CRN from the authenticated user's tracked list.

**Response:**
```json
{
  "message": "CRN removed successfully",
  "crn": "12345"
}
```

### GET /crn/{crn}
Get information about a specific CRN.

**Response:**
```json
{
  "crn": "12345",
  "course_info": {
    "course_id": "CS 1331",
    "course_name": "Introduction to Object-Oriented Programming",
    "course_section": "A"
  },
  "tracked_by": 3
}
```

### POST /register-push
Register the user's device/browser for push notifications.

**Request Body:**
```json
{
  "push_subscription": {
    "endpoint": "https://fcm.googleapis.com/fcm/send/...",
    "keys": {
      "p256dh": "your-p256dh-key",
      "auth": "your-auth-key"
    }
  }
}
```

**Response:**
```json
{
  "message": "Push notification registration successful"
}
```

## DynamoDB Schema

### reapergt-dynamo-users
- **user_id** (String, Primary Key): Cognito user sub
- **crns** (Set): Set of CRNs tracked by the user
- **push_subscription** (Map): Push notification subscription data

### reapergt-dynamo-crns
- **crn** (String, Primary Key): Course Registration Number
- **course_id** (String): Course identifier (e.g., "CS 1331")
- **course_name** (String): Full course name
- **course_section** (String): Section identifier (e.g., "A")
- **user_ids** (Set): Set of user IDs tracking this CRN

## Deployment

### Prerequisites
- AWS CLI configured
- SAM CLI installed
- Python 3.13

### Steps

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Build the application:**
   ```bash
   sam build
   ```

3. **Deploy to AWS:**
   ```bash
   sam deploy --guided
   ```

4. **Note the outputs:**
   - API Gateway URL
   - Cognito User Pool ID
   - Cognito User Pool Client ID

### Environment Variables

The following environment variables are automatically set:
- `DYNAMODB_USERS_TABLE`: DynamoDB table for users
- `DYNAMODB_CRNS_TABLE`: DynamoDB table for CRNs

## Authentication

### Setting up Cognito

1. After deployment, note the Cognito User Pool ID and Client ID from the outputs
2. Create users in the Cognito User Pool
3. Configure your frontend to use Cognito for authentication

### JWT Token

Include the JWT token in the `Authorization` header:
```
Authorization: Bearer <your-jwt-token>
```

## Testing

Use the provided `test_api.py` script to test the endpoints:

1. Update the `API_BASE_URL` and `COGNITO_TOKEN` variables
2. Run the script:
   ```bash
   python test_api.py
   ```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200`: Success
- `400`: Bad request (validation errors)
- `401`: Unauthorized (invalid/missing token)
- `404`: Not found
- `500`: Internal server error

Error responses include a descriptive message:
```json
{
  "error": "Invalid CRN format. Must be 5 digits."
}
```

## CORS

The API is configured with CORS headers to allow cross-origin requests:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET,POST,DELETE,OPTIONS`
- `Access-Control-Allow-Headers: Content-Type,Authorization`

## Background Processing

The existing background processing system (Dispatcher, Scraper, Notifier) is preserved and will continue to monitor CRNs and send notifications.

## Security

- All endpoints require Cognito JWT authentication
- DynamoDB tables use least-privilege IAM policies
- Secrets are stored in AWS Secrets Manager
- CORS is properly configured

## Monitoring

- CloudWatch logs are enabled for all Lambda functions
- API Gateway provides request/response logging
- DynamoDB metrics are available in CloudWatch

## Troubleshooting

### Common Issues

1. **Authentication errors**: Ensure the JWT token is valid and not expired
2. **CRN validation errors**: Check that the CRN exists in OSCAR for the current term
3. **DynamoDB errors**: Verify the table names and IAM permissions
4. **CORS errors**: Check that the frontend is sending the correct headers

### Logs

Check CloudWatch logs for detailed error information:
```bash
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/reapergt"
```

## Development

### Local Testing

To test locally with SAM:
```bash
sam local start-api
```

### Adding New Endpoints

1. Add the endpoint logic to `src/app.py`
2. Update the API Gateway definition in `template.yaml`
3. Test with the provided test script
4. Deploy with `sam deploy` 