# Reaper API

Official backend API for the Reaper course tracking application. This serverless application helps Georgia Tech students track course availability and receive notifications when seats open up.

## Project Structure

- `reaper_api/` - Main Lambda function code for the API
- `events/` - Test events for local development
- `tests/` - Unit and integration tests
- `template.yaml` - AWS SAM template defining infrastructure
- `samconfig.toml` - SAM deployment configuration

## Features

- **Course Tracking**: Add/remove CRNs to track course availability
- **Real-time Notifications**: Push notifications when courses open up
- **Google Authentication**: Secure user authentication via Google OAuth
- **Health Monitoring**: Built-in health check endpoint
- **Scalable Architecture**: Serverless design with DynamoDB and Lambda

## API Endpoints

### Public Endpoints
- `GET /health` - Health check (no authentication required)

### Authenticated Endpoints
- `GET /crns` - Get user's tracked CRNs
- `POST /crns` - Add a new CRN to track
- `DELETE /crns/{crn}` - Remove a CRN from tracking
- `POST /register-push` - Register for push notifications
- `POST /test-notification` - Send a test notification

## Prerequisites

- AWS CLI configured with appropriate permissions
- SAM CLI installed
- Python 3.12
- Docker (for local testing)

## Deployment

### Quick Deploy
```bash
sam build
sam deploy --no-confirm-changeset
```

### First Time Setup
```bash
sam build
sam deploy --guided
```

### Configuration
The deployment uses the following stack configuration:
- **Stack Name**: `reaper`
- **Region**: `us-east-1`
- **DynamoDB Tables**: `reaper-users`, `reaper-crns`
- **Secrets**: `reaper-secrets` (contains VAPID keys)

## Local Development

### Build and Test Locally
```bash
# Build the application
sam build

# Start local API
sam local start-api

# Test the health endpoint
curl http://localhost:3000/health
```

### Run Tests
```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run unit tests
python -m pytest tests/unit -v

# Run integration tests (requires deployed stack)
AWS_SAM_STACK_NAME="reaper" python -m pytest tests/integration -v
```

## Environment Variables

The Lambda function uses these environment variables:
- `DYNAMODB_USERS_TABLE` - DynamoDB table for user data
- `DYNAMODB_CRNS_TABLE` - DynamoDB table for CRN tracking

## Security

- Google JWT token validation for all authenticated endpoints
- IAM roles with least-privilege access
- Secrets stored in AWS Secrets Manager
- CORS enabled for frontend integration

## Monitoring

- CloudWatch logs for all Lambda functions
- Application Insights enabled
- Health check endpoint for uptime monitoring

## Cleanup

To delete the deployed application:
```bash
sam delete --stack-name reaper
```

## Related Resources

- [Frontend Repository](../frontend/) - React PWA frontend
- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [Georgia Tech OSCAR](https://oscar.gatech.edu/) - Course registration system
