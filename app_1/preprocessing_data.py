import os
import pandas as pd
import ast
from collections import defaultdict, Counter
import logging
from .anomaly_config import anomaly_rules_config
from .helper_functions import (
    detect_anomalies,
    generate_anomaly_log,
    generate_and_write_anomaly_summary,
    generate_overall_summary,
    generate_data_point_log,
    collect_prefix_events,
    generate_updates_per_peer_info,
    generate_updates_per_prefix_info,
    collect_policy_info,
    generate_policy_log,
    write_logs_to_file,
    generate_policy_summary
)

numeric_columns = [
    'Total Routes', 'New Routes', 'Withdrawals', 'Origin Changes', 'Route Changes',
    'Maximum Path Length', 'Average Path Length', 'Maximum Edit Distance', 'Average Edit Distance',
    'Announcements', 'Unique Prefixes Announced', 'Average MED', 'Average Local Preference',
    'Total Communities', 'Unique Communities', 'Total Updates', 'Average Updates per Peer',
    'Max Updates from a Single Peer', 'Min Updates from a Single Peer', 'Std Dev of Updates',
    'Total Prefixes Announced', 'Average Announcements per Prefix',
    'Max Announcements for a Single Prefix', 'Min Announcements for a Single Prefix',
    'Std Dev of Announcements', 'Count of Unexpected ASNs in Paths',
    'Target Prefixes Withdrawn', 'Target Prefixes Announced', 'AS Path Changes',
    'Average Prefix Length', 'Max Prefix Length', 'Min Prefix Length',
    'AS Path Prepending'
]

def process_bgp(
    df,
    output_dir='processed_output',
    overall_summary_filename='overall_summary.txt',
    data_point_logs_filename='data_point_logs.txt',
    prefix_announcements_filename='target_prefix_announcements.txt',
    prefix_withdrawals_filename='target_prefix_withdrawals.txt',
    updates_per_peer_filename='updates_per_peer.txt',
    updates_per_prefix_filename='updates_per_prefix.txt',
    anomaly_summary_filename='anomaly_summary.txt',
    anomalies_filename='anomalies.txt',
    policy_summary_filename='policy_summary.txt',
    top_n_peers=5,       # Number of top peers to include in the overall summary
    percentile=90        # Percentile for high anomalies
):
    global numeric_columns
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Setup logging
    log_file = os.path.join(output_dir, 'process_bgp.log')
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s:%(message)s'
    ) 

    # Convert numeric columns to float and fill missing columns
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        else:
            logging.warning(f"Column '{col}' not found in the DataFrame. Filling with 0.0.")
            df[col] = 0.0

    # Define peer and prefix columns
    peer_columns = [f'Top Peer {i} ASN' for i in range(1, 6)]
    prefix_columns = [f'Top Prefix {i}' for i in range(1, 6)]
    peer_update_columns = [f'Top Peer {i} Updates' for i in range(1, 6)]
    prefix_update_columns = [f'Top Prefix {i} Updates' for i in range(1, 6)]

    # Process Peer Columns
    for col in peer_columns:
        if col in df.columns:
            # Convert to string to handle uniformly and remove any decimal points if present
            df[col] = df[col].apply(lambda x: str(int(x)) if pd.notnull(x) and str(x).replace('.', '', 1).isdigit() else '')
        else:
            logging.warning(f"Column '{col}' not found in the DataFrame. Filling with empty strings.")
            df[col] = ''

    # Process Prefix Columns
    for col in prefix_columns:
        if col in df.columns:
            # Ensure prefixes are strings and strip any whitespace
            df[col] = df[col].astype(str).str.strip()
            # Replace 'nan' strings with empty strings
            df[col] = df[col].replace('nan', '')
        else:
            logging.warning(f"Column '{col}' not found in the DataFrame. Filling with empty strings.")
            df[col] = ''

    # Process Update Count Columns for Peers
    for col in peer_update_columns:
        if col not in df.columns:
            df[col] = 0.0
            logging.warning(f"Column '{col}' not found in the DataFrame. Filling with 0.0.")

    # Process Update Count Columns for Prefixes
    for col in prefix_update_columns:
        if col not in df.columns:
            df[col] = 0.0
            logging.warning(f"Column '{col}' not found in the DataFrame. Filling with 0.0.")

    # Process 'Community Values' column
    if 'Community Values' in df.columns:
        df['Community Values'] = df['Community Values'].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else []
        )
    else:
        logging.warning("Column 'Community Values' not found in the DataFrame. Filling with empty lists.")
        df['Community Values'] = [[] for _ in range(len(df))]

    # Initialize summary metrics
    summary_metrics = {
        col: {
            'min': df[col].min(),
            'max': df[col].max(),
            'average': df[col].mean(),
            'std_dev': df[col].std()
        }
        for col in numeric_columns
    }

    # Calculate percentile-based thresholds
    anomaly_thresholds = {}
    for col in numeric_columns:
        if col == 'Total Routes':
            anomaly_thresholds[col] = df[col].quantile(0.05)  # Lower 5th percentile for low values
        else:
            anomaly_thresholds[col] = df[col].quantile(percentile / 100)

    # Define anomaly rules
    anomaly_rules = []
    for anomaly_rule in anomaly_rules_config:
        rule_copy = anomaly_rule.copy()
        # Deep copy the conditions to avoid mutating the original config
        rule_copy['conditions'] = [condition.copy() for condition in anomaly_rule['conditions']]
        for condition in rule_copy['conditions']:
            feature = condition['feature']
            operator_str = condition['operator']
            # Assign threshold based on percentile calculations
            threshold = anomaly_thresholds.get(feature, condition['threshold'])  # Fallback to predefined
            condition['threshold'] = threshold
        anomaly_rules.append(rule_copy)
        
    # Calculate total updates per peer
    total_updates_per_peer = defaultdict(float)
    
        # Calculate 'Average Updates per Prefix' if not present
    if 'Average Updates per Prefix' not in df.columns:
        df['Average Updates per Prefix'] = df['Total Updates'] / df['Total Prefixes Announced']
        # Handle division by zero or NaN values
        df['Average Updates per Prefix'] = df['Average Updates per Prefix'].fillna(0.0)
        logging.info("Calculated 'Average Updates per Prefix' as Total Updates divided by Total Prefixes Announced.")

    # Initialize logs and lists
    data_point_logs = []
    anomalies = []
    prefix_announcements = []
    prefix_withdrawals = []
    updates_per_peer_info = []
    updates_per_prefix_info = []
    policy_logs = []

    # Process each data point
    for idx, row in df.iterrows():
        try:
            timestamp = row.get('Timestamp', 'N/A')
            as_number = row.get('Autonomous System Number', 'N/A')

            # Generate data point log
            log_entry = generate_data_point_log(row, timestamp, as_number)
            data_point_logs.append(log_entry + "\n")

            # Collect prefix announcements and withdrawals
            collect_prefix_events(row, idx, timestamp, as_number, prefix_announcements, prefix_withdrawals)
            
            # Extract ASN values from Top Peer columns
            peer_asns = [str(int(row[col])) for col in peer_columns if row[col] and str(row[col]).replace('.', '', 1).isdigit()]
            
            # Extract corresponding update counts for peers
            peer_updates = [row[col] for col in peer_update_columns]
            logging.debug(f"Row {idx}: Top Peers Updates: {peer_updates}")
            
            # Accumulate updates per peer
            for asn, updates in zip(peer_asns, peer_updates):
                total_updates_per_peer[asn] += updates
                logging.debug(f"Accumulated {updates} updates for ASN {asn}. Total so far: {total_updates_per_peer[asn]}")
            
            # Generate updates per peer information
            updates_info = generate_updates_per_peer_info(row, timestamp, peer_asns)
            updates_per_peer_info.append(updates_info + "\n")

            # Extract Top Prefixes
            top_prefixes = [row[col] for col in prefix_columns if row[col]]
            logging.debug(f"Row {idx}: Top Prefixes: {top_prefixes}")

            # Extract corresponding update counts for prefixes
            prefix_updates = [row[col] for col in prefix_update_columns]
            logging.debug(f"Row {idx}: Top Prefixes Updates: {prefix_updates}")
            
            # Generate updates per prefix information
            updates_prefix_info = generate_updates_per_prefix_info(timestamp, top_prefixes, prefix_updates)
            updates_per_prefix_info.append(updates_prefix_info + "\n")
            logging.debug(f"Row {idx}: Updates per prefix info added.")
            
            # Detect and store anomalies
            anomalies_detected = detect_anomalies(row, anomaly_rules, require_all_conditions=False)
            if anomalies_detected:
                for anomaly in anomalies_detected:
                    anomaly_entry = {
                        'timestamp': timestamp,
                        'as_number': as_number,
                        'type': anomaly['type'],
                        'description': anomaly['description'],
                        'features_triggered': anomaly['features_triggered'],
                        'details': anomaly['details']
                    }
                    anomalies.append(anomaly_entry)

            # Collect policy-related information
            policy_info = collect_policy_info(row)
            if policy_info:
                policy_log = generate_policy_log(policy_info, timestamp, as_number)
                policy_logs.append(policy_log)
        
        except Exception as e:
            logging.error(f"Error processing row {idx}: {e}")
            continue
        
    # Write logs to files
    write_logs_to_file(data_point_logs, output_dir, data_point_logs_filename)
    write_logs_to_file(prefix_announcements, output_dir, prefix_announcements_filename)
    write_logs_to_file(prefix_withdrawals, output_dir, prefix_withdrawals_filename)
    write_logs_to_file(updates_per_peer_info, output_dir, updates_per_peer_filename)
    write_logs_to_file(updates_per_prefix_info, output_dir, updates_per_prefix_filename)
    
         # Generate Overall Summary
    overall_summary_text = generate_overall_summary(df, summary_metrics, total_updates_per_peer, top_n_peers)

    # Write Overall Summary to File
    with open(os.path.join(output_dir, overall_summary_filename), 'w', encoding='utf-8') as f:
        f.write(overall_summary_text)
        
    # Write detailed anomaly logs
    with open(os.path.join(output_dir, anomalies_filename), 'w', encoding='utf-8') as f:
        for anomaly in anomalies:
            anomaly_log = generate_anomaly_log(anomaly, anomaly['timestamp'], anomaly['as_number'])
            f.write(anomaly_log)
            
    write_logs_to_file(policy_logs, output_dir, policy_summary_filename)

    # Generate and write Anomaly Summary
    generate_and_write_anomaly_summary(anomalies, output_dir, anomaly_summary_filename)

    # Generate and write Policy Summary
    policy_summary_text = generate_policy_summary(df, summary_metrics)
    with open(os.path.join(output_dir, policy_summary_filename), 'a', encoding='utf-8') as f:
        f.write(policy_summary_text)

    print(f"Data processing complete. Output files are saved in the '{output_dir}' directory.")