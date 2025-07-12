import json

import pytest

from app_function import app


@pytest.fixture()
def health_check_event():
    """ Generates API GW Event for health check"""

    return {
        "resource": "/health",
        "path": "/health",
        "httpMethod": "GET",
        "headers": {
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        "requestContext": {
            "resourceId": "123456",
            "apiId": "1234567890",
            "resourcePath": "/health",
            "httpMethod": "GET",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "accountId": "123456789012",
            "stage": "prod",
        },
        "queryStringParameters": None,
        "pathParameters": None,
        "stageVariables": None,
        "body": None,
        "isBase64Encoded": False
    }


@pytest.fixture()
def crns_get_event():
    """ Generates API GW Event for CRNs GET request (no auth header)"""

    return {
        "resource": "/crns",
        "path": "/crns",
        "httpMethod": "GET",
        "headers": {
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        "requestContext": {
            "resourceId": "123456",
            "apiId": "1234567890",
            "resourcePath": "/crns",
            "httpMethod": "GET",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "accountId": "123456789012",
            "stage": "prod",
        },
        "queryStringParameters": None,
        "pathParameters": None,
        "stageVariables": None,
        "body": None,
        "isBase64Encoded": False
    }


def test_health_endpoint(health_check_event):
    """Test the health check endpoint"""

    ret = app.lambda_handler(health_check_event, "")
    data = json.loads(ret["body"])

    assert ret["statusCode"] == 200
    assert data["status"] == "healthy"
    assert data["service"] == "Reaper API"
    assert "version" in data
    assert "timestamp" in data


def test_crns_endpoint_requires_auth(crns_get_event):
    """Test that CRNs endpoint requires authentication"""

    ret = app.lambda_handler(crns_get_event, "")
    data = json.loads(ret["body"])

    assert ret["statusCode"] == 401
    assert "error" in data
    assert "Missing authorization header" in data["error"]
