anomaly_rules_config = [
    # Leak Anomaly
    {
        'type': 'Leak Anomaly',
        'description': "Excessive route withdrawals or unexpected route advertisements indicating possible route leaks.",
        'conditions': [
            {'feature': 'Withdrawals', 'operator': '>', 'threshold': None},
            {'feature': 'Route Changes', 'operator': '>', 'threshold': None}
        ]
    },
    # Flapping Anomaly
    {
        'type': 'Flapping Anomaly',
        'description': "Frequent changes in route announcements and withdrawals, indicating network instability.",
        'conditions': [
            {'feature': 'Std Dev of Updates', 'operator': '>', 'threshold': None},
            {'feature': 'Announcements', 'operator': '>', 'threshold': None}
        ]
    },
    # Hijack Anomaly
    {
        'type': 'Hijack Anomaly',
        'description': "Unauthorized ASNs appearing in the AS path, indicating potential route hijacking.",
        'conditions': [
            {'feature': 'Count of Unexpected ASNs in Paths', 'operator': '>', 'threshold': None}
        ]
    },
    # Path Manipulation Anomaly
    {
        'type': 'Path Manipulation Anomaly',
        'description': "Unusual modifications to the AS path, such as excessive AS path prepending.",
        'conditions': [
            {'feature': 'AS Path Prepending', 'operator': '>', 'threshold': None},
            {'feature': 'Maximum Path Length', 'operator': '>', 'threshold': None}
        ]
    },
    # Policy-Related Anomaly
    {
        'type': 'Policy-Related Anomaly',
        'description': "Deviations from defined routing policies, such as unexpected MED or Local Preference values.",
        'conditions': [
            {'feature': 'Average MED', 'operator': '>', 'threshold': None},
            {'feature': 'Average Local Preference', 'operator': '<', 'threshold': None}
        ]
    },
    # Add more anomaly categories and their conditions as needed
]