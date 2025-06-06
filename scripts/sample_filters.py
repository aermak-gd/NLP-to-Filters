SAMPLE_FILTERS = [
    {
        "displayName": "Client First Name",
        "type": "STRING",
        "controlType": "TEXT_INPUT",
        "operators": ["EQUALS", "CONTAINS", "STARTS_WITH", "ENDS_WITH"],
        "category": "Client",
        "description": "First Name of the client",
        "keywords": ["name", "client name", "first name"]
    },
    {
        "displayName": "Client Family Name",
        "type": "STRING",
        "controlType": "TEXT_INPUT",
        "operators": ["EQUALS", "CONTAINS", "STARTS_WITH", "ENDS_WITH"],
        "category": "Client",
        "description": "Family name of the client",
        "keywords": ["last name", "full name"]
    },
    {
        "displayName": "Client Email",
        "type": "STRING",
        "controlType": "TEXT_INPUT",
        "operators": ["EQUALS", "CONTAINS", "STARTS_WITH", "ENDS_WITH"],
        "category": "Contact Information",
        "description": "Email address of the client",
        "keywords": ["email", "contact", "email address", "mail"]
    },
    {
        "displayName": "Account Number",
        "type": "STRING",
        "controlType": "TEXT_INPUT",
        "operators": ["EQUALS", "STARTS_WITH", "CONTAINS"],
        "category": "Account",
        "description": "Unique identifier for the client's account",
        "keywords": ["account", "account ID", "number", "account number", "reference"]
    },
    {
        "displayName": "Social Security Number (SSN)",
        "type": "STRING",
        "controlType": "TEXT_INPUT",
        "operators": ["EQUALS"],
        "category": "Client Identification",
        "description": "Social Security Number of the client. Access to this filter should be highly restricted and logged due to its sensitive nature.",
        "keywords": ["SSN", "social security", "identification", "tax ID"]
    },
    {
        "displayName": "Social Security Number (SSN) 2",
        "type": "STRING",
        "controlType": "TEXT_INPUT",
        "operators": ["EQUALS"],
        "category": "Client Identification",
        "description": "Social Security Number of the client. Access to this filter should be highly restricted and logged due to its sensitive nature.",
        "keywords": ["SSN", "social security", "identification", "tax ID"]
    },
    {
        "displayName": "Client Age",
        "type": "NUMBER",
        "controlType": "NUMBER_RANGE",
        "operators": ["GREATER_THAN", "LESS_THAN", "EQUALS", "BETWEEN"],
        "category": "Client",
        "description": "Age of the client",
        "keywords": ["age", "years old", "older", "younger"]
    },
    {
        "displayName": "Marital Status",
        "type": "STRING",
        "controlType": "CHECKBOX",
        "options": ["Single", "Married", "Divorced", "Widowed"],
        "category": "Client",
        "description": "Marital status of the client",
        "keywords": ["married", "single", "divorced", "widowed", "marital"]
    },
    {
        "displayName": "Last Contact Date",
        "type": "DATE",
        "controlType": "DATE_RANGE",
        "operators": ["WITHIN", "NOT_WITHIN", "EQUALS", "GREATER_THAN", "LESS_THAN"],
        "category": "CRM Activities",
        "description": "Date of last contact with client",
        "keywords": ["contact", "last contacted", "communication", "outreach"]
    },
    {
        "displayName": "Account Balance",
        "type": "NUMBER",
        "controlType": "NUMBER_RANGE",
        "operators": ["GREATER_THAN", "LESS_THAN", "EQUALS", "BETWEEN"],
        "category": "Account",
        "description": "Current account balance",
        "keywords": ["balance", "account value", "portfolio value", "assets"]
    },
    {
        "displayName": "Income Level",
        "type": "NUMBER",
        "controlType": "NUMBER_RANGE",
        "operators": ["GREATER_THAN", "LESS_THAN", "EQUALS", "BETWEEN"],
        "category": "Client",
        "description": "Annual income of the client",
        "keywords": ["income", "salary", "earnings", "annual income"]
    },
    {
        "displayName": "Investment Risk Tolerance",
        "type": "STRING",
        "controlType": "CHECKBOX",
        "options": ["Conservative", "Moderate", "Aggressive"],
        "category": "Investment",
        "description": "Client's risk tolerance for investments",
        "keywords": ["risk", "tolerance", "conservative", "aggressive", "moderate"]
    }
]