# Dataset

This directory contains test case datasets in JSON format for various websites. Each JSON file represents a collection of web UI test scenarios for automated testing research.

## Dataset Structure

Each JSON file follows this structure:

```json
{
  "testcases": [
    {
      "prompt": {
        "name": "Test Case Name",
        "instruction": "Base URL and test execution instruction",
        "description": "Brief description of what the test case does",
        "input": {
          "search_input": "Input data or parameters needed",
          "action": "Step-by-step actions to perform"
        },
        "expected": {
          "outcome": "Expected result after test execution",
          "status": "Success/Failure status"
        },
        "category": "Test category (e.g., Search & Filter, Information Retrieval)"
      }
    }
  ]
}
```

## Website Coverage

The dataset includes test cases for 19 different websites:

- **amtrak.json** - Train booking and status checking
- **archivestore.json** - Digital archive browsing
- **cdc.json** - Health information search
- **cse_buet.json** - Academic department website
- **devto.json** - Developer community platform
- **google_blog.json** - Blog search and navigation
- **gutenberg.json** - Digital book library
- **hackerrank.json** - Coding challenge platform
- **head_gear.json** - E-commerce product browsing
- **internet_archive.json** - Digital preservation platform
- **lavishta.json** - Fashion e-commerce
- **mdn.json** - Developer documentation
- **mit_ocw.json** - Educational course platform
- **nasa.json** - Space agency information portal
- **openlibrary.json** - Open book database
- **w3schools.json** - Web development tutorials
- **who.json** - World Health Organization site
- **wikipedia.json** - Encyclopedia search and navigation
- **yc.json** - Startup accelerator platform

## Test Categories

Test cases are categorized into different types:
- **Search & Filter** - Finding and filtering content
- **Information Retrieval** - Accessing specific information
- **Navigation** - Moving through site sections
- **Form Interaction** - Filling out forms and inputs
- **E-commerce** - Product browsing and selection

## Usage

These JSON files serve as input data for:
1. Automated test script generation
2. Web UI testing research
3. Browser automation agent training
4. Cross-website functionality comparison

Each test case provides structured data that can be processed by automation tools to generate executable test scripts for the corresponding websites.