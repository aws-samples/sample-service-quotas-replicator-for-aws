# Sample Service Quotas Replicator for AWS

This repository contains sample code for the AWS Quota Replicator (AQR) tool, which demonstrates how to build a solution for comparing and managing service quotas across AWS accounts and regions.

**Note: AQR is proudly built with the powerful assistance of [Amazon Q Developer!](https://aws.amazon.com/q/developer/)**

## Overview

The AWS Quota Replicator (AQR) is a sample Streamlit application that allows users to compare service quotas between different AWS accounts and regions. It helps identify differences in quota configurations, which is particularly useful for account migrations, environment parity checks, and capacity planning.

## Use Cases

- **Account Migration**: When migrating workloads from one AWS account to another, ensure the destination account has the necessary quota limits to support your applications.
  
- **Environment Parity**: Maintain consistency between development, testing, staging, and production environments by replicating quota configurations.
  
- **Multi-Region Deployments**: Ensure consistent quota configurations across multiple AWS regions for global applications.
  
- **Disaster Recovery Planning**: Verify that your DR region has the same quota limits as your primary region to support failover scenarios.
  
- **Capacity Planning**: Proactively identify quota constraints before they impact your ability to scale resources.
  
## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│            Sample AWS Service Quota Replicator Tool             │
│                                                                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit Interface                      │
└───────┬─────────────────────────────────────────────────┬───────┘
        │                                                 │
        ▼                                                 ▼
┌───────────────────┐                           ┌───────────────────┐
│  Source Account   │                           │Destination Account│
│  Quota Retrieval  │◄──┐                   ┌──►│  Quota Retrieval  │
└────────┬──────────┘   │                   │   └────────┬──────────┘
         │              │                   │            │
         ▼              │                   │            ▼
┌───────────────────┐   │  Parallel         │   ┌───────────────────┐
│   AWS Service     │   │  Processing       │   │   AWS Service     │
│   Quotas API      │   │                   │   │   Quotas API      │
└────────┬──────────┘   │                   │   └────────┬──────────┘
         │              │                   │            │
         ▼              │                   │            ▼
┌───────────────────┐   │                   │   ┌───────────────────┐
│  Cache System     │───┘                   └───│  Cache System     │
└────────┬──────────┘                           └────────┬──────────┘
         │                                               │
         └───────────────────┬───────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Quota Comparison                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Results Display                           │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐    │
│  │ Summary Stats │  │ Different     │  │ Quota Increase    │    │
│  │               │  │ Quotas        │  │ Request Interface │    │
│  └───────────────┘  └───────────────┘  └───────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Logging & Error Handling                     │
└─────────────────────────────────────────────────────────────────┘
```

This diagram illustrates the architecture of the AWS Quota Replicator Tool, showing how data flows from the AWS Service Quotas API through parallel processing paths for both source and destination accounts, through the comparison engine, and finally to the user interface.


## Features

- Compare service quotas between two AWS accounts/profiles
- Filter out default values to focus on customized quotas
- Identify services and quotas that exist only in the source account
- Highlight differences between source and destination quotas
- Request quota increases to match source account values
- Track status of submitted quota increase requests
- Cache quota data to improve performance and reduce API calls
- Clear cache functionality for refreshing data
- Parallel fetching of quota data for improved performance
- Comprehensive logging for troubleshooting and auditing

## Prerequisites

- Python 3.6+
- AWS CLI configured with profiles for the accounts you want to compare

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Ensure AWS credentials are configured in `~/.aws/credentials` or `~/.aws/config`

## Security Considerations

### AWS Permissions

- Source and destination AWS profiles should follow the principle of least privilege
- Required permissions for the application:
  - Both source and Destination profile: 
    - `servicequotas:ListServices`
    - `servicequotas:ListServiceQuotas`
    - `servicequotas:ListAWSDefaultServiceQuotas`
  
  - Destination profile:
    - `servicequotas:RequestServiceQuotaIncrease`

### Hosting Considerations

While the application is designed to run locally, if you plan to host it:

- Implement proper authentication mechanisms (e.g., OAuth, SAML)
- Enable TLS/HTTPS for all communications
- Consider implementing session management and timeouts
- Restrict access to authorized users only
- Implement proper secrets management for AWS credentials
- Consider using AWS IAM roles instead of static credentials
- Regularly audit access logs and permissions

## Usage

Run the application with:
```
streamlit run app.py
```

### Step-by-Step Guide

1. **Select Source Configuration**:
   - Choose the source AWS profile
   - Select the source AWS region

2. **Select Destination Configuration**:
   - Choose the destination AWS profile
   - Select the destination AWS region

3. **Optional Settings**:
   - Check "Suppress default values" to only show quotas that differ from AWS defaults

4. **Compare Quotas**:
   - Click the "Compare Quotas" button to start the comparison
   - The tool will fetch and compare quotas from both accounts

5. **Review Results**:
   - Summary statistics show total quotas, different quotas, adjustable quotas, and services only in source
   - Services and quotas only in the source account are displayed in a separate table
   - Different quotas are highlighted for easy identification
   - All quotas are displayed in a comprehensive table

6. **Request Quota Increases**:
   - Select quotas you want to increase in the destination account using checkboxes
   - Submit quota increase requests to match source account values
   - View submission summary with success/failure status for each request

7. **Track Quota Request Status**:
   - Click "Get Quota Status" button to check on previously submitted requests
   - Select a request ID from the dropdown to view current status
   - View detailed status information including approved, pending, and denied requests

8. **Cache Management**:
   - View cached data in the sidebar
   - Clear cache to fetch fresh data from AWS

## Project Structure

The application has been modularized for better organization and maintainability:

```
AwsQuotaReplicator/
├── app.py                  # Main application entry point
├── src/                    # Source code directory
│   ├── aws/                # AWS-related functionality
│   │   ├── comparison.py   # Quota comparison logic
│   │   ├── profiles.py     # AWS profile and region management
│   │   └── quotas.py       # Service Quotas API interaction
│   ├── ui/                 # User interface components
│   │   ├── callbacks.py    # UI callback functions
│   │   ├── components.py   # Reusable UI components
│   │   ├── formatting.py   # UI formatting utilities
│   │   ├── quota_request.py # Quota request handling
│   │   └── sidebar.py      # Sidebar components
│   └── utils/              # Utility functions
│       ├── cache.py        # Cache management
│       └── logger.py       # Logging configuration
├── logs/                   # Log files directory
|── tests/                  # Test code directory
|   |── test_app.py         # Unit tests
|   |── test_cache/         # Cache test mock data files
└── quota_cache/            # Cache directory

```

## Key Components

### Data Retrieval (`src/aws/quotas.py`)

The application uses the AWS Service Quotas API to retrieve quota information from both source and destination accounts. Data is cached to improve performance and reduce API calls. The tool implements parallel fetching to retrieve quota data from both accounts simultaneously, significantly improving performance.

### Quota Comparison (`src/aws/comparison.py`)

The tool compares quotas between accounts and identifies:
- Quotas with different values
- Quotas that exist only in the source account
- Whether quotas are adjustable

### User Interface (`src/ui/`)

The Streamlit interface provides:
- Clear selection of AWS profiles and regions
- Summary statistics for quick insights
- Interactive tables for detailed analysis
- Checkbox selection for quota increase requests
- Cache management controls

### Quota Request Handling (`src/ui/quota_request.py`)

Manages the process of:
- Submitting quota increase requests
- Tracking request status
- Displaying request history

## Cache System (`src/utils/cache.py`)

Quota data is cached in the `quota_cache` directory to:
- Reduce API calls to AWS
- Improve application performance
- Prevent rate limiting issues

Cache files are named according to the profile and region they represent.

## Logging System (`src/utils/logger.py`)

The application includes comprehensive logging to:
- Track application execution flow
- Record API calls and responses
- Capture errors and warnings
- Facilitate troubleshooting

Logs are stored in the `logs` directory with daily rotation.

## Error Handling

The application includes error handling for:
- Missing AWS credentials
- API rate limiting
- Service-specific quota retrieval failures
- Cache read/write operations
- Data conversion and serialization issues

## Best Practices

- Use the "Suppress default values" option to focus on customized quotas
- Clear the cache periodically to ensure data freshness
- Review quota differences carefully before requesting increases
- Be aware that some quotas cannot be adjusted automatically

## Troubleshooting

- If no AWS profiles are found, ensure your AWS credentials are properly configured
- If quota retrieval fails, check your AWS permissions and network connectivity
- If the application seems slow, consider using the cached data option

## Limitations

- The tool can only request increases for adjustable quotas
- Some quota increases may require AWS Support tickets and creation of support ticket is not handled by the tool. 

## Security

Contributions to improve the tool are welcome. 

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

