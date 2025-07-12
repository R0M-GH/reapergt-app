import os

import boto3
import pytest
import requests

"""
Make sure env variable AWS_SAM_STACK_NAME exists with the name of the stack we are going to test. 
"""


class TestReaperApi:

    @pytest.fixture()
    def api_gateway_url(self):
        """ Get the API Gateway URL from Cloudformation Stack outputs """
        stack_name = os.environ.get("AWS_SAM_STACK_NAME")

        if stack_name is None:
            raise ValueError('Please set the AWS_SAM_STACK_NAME environment variable to the name of your stack')

        client = boto3.client("cloudformation")

        try:
            response = client.describe_stacks(StackName=stack_name)
        except Exception as e:
            raise Exception(
                f"Cannot find stack {stack_name} \n" f'Please make sure a stack with the name "{stack_name}" exists'
            ) from e

        stacks = response["Stacks"]
        stack_outputs = stacks[0]["Outputs"]
        api_outputs = [output for output in stack_outputs if output["OutputKey"] == "ApiUrl"]

        if not api_outputs:
            raise KeyError(f"ApiUrl not found in stack {stack_name}")

        return api_outputs[0]["OutputValue"]  # Extract url from stack outputs

    def test_health_endpoint(self, api_gateway_url):
        """ Call the health endpoint and check the response """
        response = requests.get(f"{api_gateway_url}health")

        assert response.status_code == 200
        json_response = response.json()
        assert json_response["status"] == "healthy"
        assert json_response["service"] == "Reaper API"
        assert "version" in json_response
        assert "timestamp" in json_response

    def test_crns_endpoint_without_auth(self, api_gateway_url):
        """ Test that CRNs endpoint requires authentication """
        response = requests.get(f"{api_gateway_url}crns")

        assert response.status_code == 401
        json_response = response.json()
        assert "error" in json_response
        assert "Missing authorization header" in json_response["error"]
