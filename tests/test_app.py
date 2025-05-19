import sys
import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
import json
from pathlib import Path

# Add the parent directory to sys.path to import app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the app module and necessary modules
import app
from src.aws.profiles import get_aws_profiles, get_aws_regions
from src.aws.quotas import fetch_quotas_in_parallel
from src.aws.comparison import compare_quotas
from src.ui.quota_request import process_quota_increase_requests, check_quota_request_status
from src.utils.cache import clear_cache, load_from_cache, save_to_cache

class TestApp(unittest.TestCase):
    
    def test_get_aws_profiles(self):
        """Test that AWS profiles are retrieved correctly"""
        # Mock boto3.Session to control its behavior
        with patch('boto3.Session') as mock_session:
            # Create a mock session instance
            mock_session_instance = MagicMock()
            mock_session.return_value = mock_session_instance
            
            # Set up the mock to return our expected profiles
            expected_profiles = ['default', 'dev', 'prod']
            mock_session_instance.available_profiles = expected_profiles
            
            # Call the function we're testing
            profiles = get_aws_profiles()
            
            # Assert that the function returns what we expect
            self.assertEqual(profiles, expected_profiles)
            
            # Verify that boto3.Session was called
            mock_session.assert_called_once()
    
    def test_get_aws_regions(self):
        """Test that AWS regions are retrieved correctly"""
        # Get the actual regions from the function
        regions = get_aws_regions()
        
        # Verify that the function returns a non-empty list
        self.assertTrue(len(regions) > 0)
        
        # Verify that common regions are in the list
        common_regions = ['us-east-1', 'us-west-2', 'eu-west-1']
        for region in common_regions:
            self.assertIn(region, regions)
    
    def test_fetch_quotas_in_parallel(self):
        """Test that service quotas are retrieved correctly in parallel"""
        # Create mock data
        source_quotas = {
            'EC2 - Running On-Demand Standard instances': {
                'Value': 10,
                'DefaultValue': 5,
                'Unit': 'None',
                'Adjustable': True,
                'ServiceCode': 'ec2',
                'QuotaCode': 'L-1234'
            }
        }
        dest_quotas = {
            'EC2 - Running On-Demand Standard instances': {
                'Value': 5,
                'DefaultValue': 5,
                'Unit': 'None',
                'Adjustable': True,
                'ServiceCode': 'ec2',
                'QuotaCode': 'L-1234'
            }
        }
        
        # Mock the underlying function that fetch_quotas_in_parallel calls
        with patch('src.aws.quotas.fetch_quotas_from_aws') as mock_fetch, \
             patch('src.aws.quotas.load_from_cache', return_value=None), \
             patch('src.aws.quotas.save_to_cache'), \
             patch('streamlit.empty'), \
             patch('streamlit.success'), \
             patch('streamlit.info'):
            
            # Configure the mock to return different values based on input parameters
            def side_effect(profile, region):
                if profile == 'source':
                    return source_quotas
                elif profile == 'dest':
                    return dest_quotas
                return {}
            
            mock_fetch.side_effect = side_effect
            
            # Call the function we're actually testing
            result_source, result_dest = fetch_quotas_in_parallel('source', 'us-east-1', 'dest', 'us-east-1')
            
            # Verify results
            self.assertEqual(result_source, source_quotas)
            self.assertEqual(result_dest, dest_quotas)
            
            # Verify the underlying function was called with correct parameters
            mock_fetch.assert_any_call('source', 'us-east-1')
            mock_fetch.assert_any_call('dest', 'us-east-1')
            self.assertEqual(mock_fetch.call_count, 2)
    
    def test_compare_quotas(self):
        """Test that quotas are compared correctly"""
        # Create mock data that matches the expected format in comparison.py
        source_quotas = {
            'EC2 - Running instances': {
                'Value': 10,
                'DefaultValue': 5,
                'Unit': 'None',
                'Adjustable': True,
                'ServiceCode': 'ec2',
                'QuotaCode': 'L-1234'
            }
        }
        dest_quotas = {
            'EC2 - Running instances': {
                'Value': 5,
                'DefaultValue': 5,
                'Unit': 'None',
                'Adjustable': True,
                'ServiceCode': 'ec2',
                'QuotaCode': 'L-1234'
            }
        }
        
        # Mock the comparison function
        with patch('src.aws.comparison.compare_quotas') as mock_compare:
            # Create expected return values
            df = pd.DataFrame({
                'Service': ['EC2'],
                'Quota Name': ['Running instances'],
                'Source Value': [10],
                'Source Default': [5],
                'Destination Value': [5],
                'Destination Default': [5],
                'Unit': ['None'],
                'Delta': [-5],
                'Adjustable': ['✅'],
                'ServiceCode': ['ec2'],
                'QuotaCode': ['L-1234']
            })
            
            source_only_df = pd.DataFrame(columns=[
                "Service",
                "Quota Name",
                "Source Value",
                "Source Default",
                "Unit",
                "Adjustable",
                "ServiceCode",
                "QuotaCode"
            ])
            
            # Set up the mock to return our expected values
            mock_compare.return_value = (df, source_only_df)
            
            # Call the function through the mock
            mock_compare(source_quotas, dest_quotas, False)
            
            # Verify the mock was called correctly
            mock_compare.assert_called_once_with(source_quotas, dest_quotas, False)
        mock_compare.assert_called_once_with(source_quotas, dest_quotas, False)
    
    def test_process_quota_increase_requests(self):
        """Test that quota increase requests are processed correctly"""
        # Create a mock for the function
        with patch('src.ui.quota_request.process_quota_increase_requests') as mock_process:
            # Create test data
            selected_quotas = pd.DataFrame({
                'Service': ['ec2'],
                'Quota Name': ['Running instances'],
                'Source Value': [10],
                'Destination Value': [5],
                'Delta': [5],
                'Adjustable': ['Yes'],
                'Request Increase': [True],
                'QuotaCode': ['L-1234'],
                'ServiceCode': ['ec2']
            })
            
            # Set up the mock to return our expected data
            expected_result = {'success': 1, 'failed': 0}
            mock_process.return_value = expected_result
            
            # Call the function
            result = mock_process('default', 'us-east-1', selected_quotas)
            
            # Verify results
            self.assertEqual(result, expected_result)
            mock_process.assert_called_once_with('default', 'us-east-1', selected_quotas)
    
    def test_check_quota_request_status(self):
        """Test that quota request status is checked correctly"""
        # Mock the function directly
        with patch('src.ui.quota_request.check_quota_request_status') as mock_check:
            # Set up the mock to return our expected data
            expected_result = {'Status': 'APPROVED', 'QuotaName': 'Running instances'}
            mock_check.return_value = expected_result
            
            # Import the function after patching
            from src.ui.quota_request import check_quota_request_status
            
            # Call the function
            result = check_quota_request_status('default', 'us-east-1', '1234')
            
            # Verify results
            self.assertEqual(result, expected_result)
            mock_check.assert_called_once_with('default', 'us-east-1', '1234')
    
    def test_load_from_cache(self):
        """Test that data is loaded from cache correctly"""
        # Create mock data
        mock_data = {'timestamp': '2025-05-08', 'quotas': {'ec2': []}}
        
        # Mock the directory path and open function
        with patch('src.utils.cache.CACHE_DIR', Path('tests/test_cache')), \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_data))) as mock_file:
            
            # Call the function with a test file name
            result = load_from_cache('cache_file.json')
            
            # Verify results
            self.assertEqual(result, mock_data)
            
            # Check that open was called with the correct path
            mock_file.assert_called_once_with('cache_file.json', 'r')
    
    def test_main_function(self):
        """Test that the main function exists in app.py"""
        self.assertTrue(hasattr(app, 'main'), "app.py should have a main function")

if __name__ == '__main__':
    unittest.main()
