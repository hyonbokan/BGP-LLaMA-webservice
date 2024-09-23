import { createSlice } from '@reduxjs/toolkit';

const initialState = {
    allDatasets: [
            {
                title: 'Self-Instruct Generated Dataset',
                id: 'self-instruct-generated-dataset',
                datasets: [
                    {
                        id: 'bgp-knowledge',
                        title:'BGP Knowledge',
                        fileUrl: 'finetuning-dataset/self-instruct-generated-dataset/bgp-knowledge.json',
                        fileCount: 20000,
                        size: '18.1 MB',
                        fileType: 'json',
                        description: "This expanded dataset was generated using the 'Self-Instruct' framework and contains a total of 20,000 instruction-input-output pairs aimed at enriching the knowledge base of BGP (Border Gateway Protocol) for advanced pre-trained language models like GPT. The dataset serves as an extensive resource for fine-tuning models to handle complex BGP-related scenarios with greater nuance and diversity. By leveraging this comprehensive set, the model can gain a deeper understanding of BGP routing behavior, path selection, route stability, security issues, and real-time anomaly detection. The dataset is designed to provide a structured learning path that guides the LLM (Large Language Model) from foundational BGP concepts to more advanced case studies, ensuring a broad and in-depth comprehension of BGP operations. This set of instructions is intended to be used for research, network management, and anomaly detection tasks, helping models develop the ability to analyze and optimize BGP routing data effectively. The dataset emphasizes real-world applicability, capturing a wide range of BGP topics to facilitate practical knowledge transfer.",
                        categories: {
                          "1. BGP Fundamentals": "Covers the foundational principles of BGP, including how BGP functions as a path vector protocol and the basic mechanisms behind BGP route advertisements, decision processes, and convergence.",
                          
                          "2. BGP Security and Stability": "Focuses on the security challenges within BGP, such as prefix hijacking, route leaks, and methods to secure BGP routing, including RPKI (Resource Public Key Infrastructure) and filtering mechanisms.",
                          
                          "3. BGP Route Stability": "Explores the stability of BGP routes, path flapping, and the effect of route oscillation on global internet routing, including mitigation techniques such as route dampening.",
                          
                          "4. BGP Route Manipulation and Optimization": "Covers topics related to BGP route manipulation through policies and attributes such as local preference, MED, and AS-path prepending to optimize traffic flow and network performance.",
                          
                          "5. BGP Analysis and Anomaly Detection": "Focuses on detecting anomalies in BGP routing, such as route hijacks, leaks, and malicious activities, using tools and methods to analyze routing tables and BGP announcements.",
                          
                          "6. BGP Session Establishment and Maintenance": "Details the processes involved in establishing and maintaining BGP sessions between peers, including TCP connection setup, keepalive messages, and session termination.",
                          
                          "7. BGP Peer Grouping and Configuration": "Explains how BGP peer groups can be used to simplify configuration and enhance the scalability of routing policies, especially in large-scale networks.",
                          
                          "8. BGP Address Families": "Explores different BGP address families such as IPv4, IPv6, and VPNv4, and their respective roles in routing multiple protocol families within BGP.",
                          
                          "9. BGP Policies and Route Maps": "Covers the use of route maps, prefix lists, and filter policies to control the advertisement and acceptance of routes, and how these policies affect global routing decisions.",
                          
                          "10. BGP Multihoming and Load Balancing": "Examines how BGP is used for multihoming to improve redundancy and reliability in networks, including load balancing techniques across multiple ISPs.",
                          
                          "11. BGP Troubleshooting and Diagnostics": "Details tools and techniques for diagnosing and troubleshooting BGP issues, such as using BGP debugs, route tracing, and route validation to identify misconfigurations or network problems.",
                          
                          "12. BGP Case Studies and Real-World Examples": "Presents real-world BGP incidents and case studies, such as high-profile BGP hijacks or outages, and explains how these events impacted global routing and network stability."
                        },
                        jsonSnapshot: {
                            "instruction": "Discuss the challenges of debugging BGP issues and the best practices for troubleshooting BGP sessions.",
                            "input": "Our service provider reported a communication issue between two BGP routers.",
                            "output": "Debugging BGP issues can be complex and time-consuming due to configuration complexity, state issues, and the distributed nature of BGP. It is important to understand the best practices for troubleshooting BGP sessions. It is best to start by verifying the basic connectivity and ICMP echo responses, followed by examining route health scores and dampened routes. Next, verify that BGP peers are established and peering correctly by analyzing BGP updates, routes, and timers. Finally, focus on stabilizing the BGP session to prevent routing instabilities. A combination of BGP debugging tools, such as TCPdump, show ip bgp, and show ip route, can prove invaluable in this process."
                        },
                    },
                    {   
                        id: 'pybgpstream-base',
                        title:'PyBGPStream Base',
                        fileUrl: '/finetuning-dataset/self-instruct-generated-dataset/pybgpstream-base.json',
                        fileCount: 8609,
                        size: '27.5 MB',
                        fileType: 'json',
                        description: "This dataset is an expanded version, enhanced using the 'Self-Instruct' framework to leverage advanced Large Language Models (LLMs) for generating additional tasks and diversifying the dataset. It combines manually curated seed tasks with real BGP hijacking and anomaly cases, offering a comprehensive set of 8,609 tasks for BGP data collection and analysis using the PyBGPStream library. The dataset contains scripts designed to extract relevant features, conduct detailed analysis, and generate visualizations for comprehensive insight into BGP anomalies. These tasks demonstrate the essential utilization of PyBGPStream, guiding the LLM through the necessary syntax and workflows required to handle BGP data effectively, including real-time data processing, feature extraction, anomaly detection, and global routing behavior analysis. The inclusion of real cases of BGP anomalies is crucial for training and research purposes, as it provides a realistic understanding of how such events manifest in real-world scenarios. While synthetic data often lacks the complexity and nuances of genuine incidents, this dataset allows researchers and analysts to train models on actual BGP hijacking and anomaly cases, resulting in more robust anomaly detection systems, enhanced network security, and improved resilience against potential routing disruptions. This foundational set not only helps the LLM generate additional tasks but also expands its capacity to work with BGP data and tools in diverse, real-world scenarios, ensuring accurate detection and mitigation strategies.",
                        jsonSnapshot: {                           
                            "instruction": "Identify the MOASes that announce AS 2497 and determine the path inflation.",
                            "input": "ASN: 2497\nFilter: path \"_2497_\"",
                            "output": "import pybgpstream\nfrom collections import Counter\n\nstream = pybgpstream.BGPStream(\n    from_time=\"2020-10-01 00:00:00\",\n    until_time=\"2020-10-31 00:00:00\",\n    collectors=[\"route-views2\", \"route-views3\", \"route-views4\", \"ris-ripe\"],\n    record_type=\"updates\",\n    filter=\"path \\\"_2497_\\\"\"\n)\n\nas_paths = []\n\nfor rec in stream.records():\n    for elem in rec:\n      if elem.type == \"A\":\n        as_paths.append(elem.fields[\"as-path\"].split()[0])\n\nmoases = Counter(as_paths).most_common()\n\n# Calculate path inflation\npath_inflation = 0\nfor moas in moases:\n    path_inflation += (moas[1] - 1)\n\nprint(f\"MOASes: {moases}\")\nprint(f\"Path inflation for AS 2497: {path_inflation}\")",
                        },
                    },
                    {   
                        id: 'pybgpstream-real-time',
                        title:'PyBGPStream Real-time Stream',
                        fileUrl: '/finetuning-dataset/self-instruct-generated-dataset/pybgpstream-real-time.json',
                        fileCount: 1501,
                        size: '4.5 MB',
                        fileType: 'json',
                        description: 'This dataset provides an expanded version of real BGP hijacking and anomaly cases, enriched with more diverse examples using the "Self-Instruct" framework. By leveraging advanced Large Language Models (LLMs), the dataset has been significantly increased in both count and variety, offering a broader range of BGP anomaly scenarios. Real-time BGP scripts designed to extract relevant features from the BGP data, conduct in-depth analysis, and create visualizations for better understanding. This expanded dataset is particularly valuable for training and research as it introduces a wider spectrum of real-world BGP events, ensuring that analysis models are well-equipped to recognize and respond to various anomalies in live network environments. This enhanced diversity leads to more accurate anomaly detection, improved network security, and a deeper comprehension of BGP behavior in real-world settings.',
                        jsonSnapshot: {
                            "instruction": "Access live RPKI information from RIPE NCC for the Autonomous System (AS 2856).",
                            "input": "AS Number: 2856",
                            "output": "import pybgpstream\nasn=\"AS2856\"\nstream = pybgpstream.BGPStream(\n    project=\"rpki\",\n    record_type=\"roas\",\n    filter=\"type rpki and registered 'false' and asn '{}'\".format(asn)\n)\nfor rec in stream.records():\n    elem = rec.get_next_elem()\n    while elem:\n        print(elem.fields['prefix'])\n        elem = rec.get_next_elem()",
                        },
                    },
                ],
            },
            {
                title: 'Manual Seed Tasks',
                id: 'manual-seed-dataset',
                datasets: [
                    {
                        id: 'bgp-knowledge-1',
                        title:'BGP Knowledge I',
                        fileUrl: '/finetuning-dataset/manual-seed-dataset/bgp-knowledge-1.jsonl',
                        promptUrl: '/finetuning-dataset/manual-seed-dataset/prompt_knowledge.txt',
                        fileCount: 121,
                        size: '115 KB',
                        fileType: 'jsonl',
                        promptType: 'txt',
                        description: "This dataset contains manually curated instruction-input-output pairs aimed at expanding the BGP (Border Gateway Protocol) knowledge base for advanced pre-trained language models like GPT. The dataset serves as a foundation for generating similar tasks that will help fine-tune models for complex BGP-related scenarios. By leveraging these initial seeds, the model can generate diverse and nuanced tasks related to BGP routing behavior, path selection, route stability, security issues, and real-time anomaly detection. The primary objective is to create a structured learning resource that helps the LLM (Large Language Model) understand BGP operations from fundamental principles to advanced case studies. This dataset is carefully designed to capture a wide range of BGP topics and provide both instructional value and real-world applicability in the context of network analysis, optimization, and security. \nThe inclusion of rules within the base prompt ensures consistency and relevance in the model-generated tasks, maintaining focus on BGP-specific domains. The generated tasks are expected to aid in research, network management, and anomaly detection tasks involving BGP routing data.",
                        categories: {
                                "1. BGP Fundamentals": "Covers the foundational principles of BGP, including how BGP functions as a path vector protocol and the basic mechanisms behind BGP route advertisements, decision processes, and convergence.",
                                
                                "2. BGP Security and Stability": "Focuses on the security challenges within BGP, such as prefix hijacking, route leaks, and methods to secure BGP routing, including RPKI (Resource Public Key Infrastructure) and filtering mechanisms.",
                                
                                "3. BGP Route Stability": "Explores the stability of BGP routes, path flapping, and the effect of route oscillation on global internet routing, including mitigation techniques such as route dampening.",
                                
                                "4. BGP Route Manipulation and Optimization": "Covers topics related to BGP route manipulation through policies and attributes such as local preference, MED, and AS-path prepending to optimize traffic flow and network performance.",
                                
                                "5. BGP Analysis and Anomaly Detection": "Focuses on detecting anomalies in BGP routing, such as route hijacks, leaks, and malicious activities, using tools and methods to analyze routing tables and BGP announcements.",
                                
                                "6. BGP Session Establishment and Maintenance": "Details the processes involved in establishing and maintaining BGP sessions between peers, including TCP connection setup, keepalive messages, and session termination.",
                                
                                "7. BGP Peer Grouping and Configuration": "Explains how BGP peer groups can be used to simplify configuration and enhance the scalability of routing policies, especially in large-scale networks.",
                                
                                "8. BGP Address Families": "Explores different BGP address families such as IPv4, IPv6, and VPNv4, and their respective roles in routing multiple protocol families within BGP.",
                                
                                "9. BGP Policies and Route Maps": "Covers the use of route maps, prefix lists, and filter policies to control the advertisement and acceptance of routes, and how these policies affect global routing decisions.",
                                
                                "10. BGP Multihoming and Load Balancing": "Examines how BGP is used for multihoming to improve redundancy and reliability in networks, including load balancing techniques across multiple ISPs.",
                                
                                "11. BGP Troubleshooting and Diagnostics": "Details tools and techniques for diagnosing and troubleshooting BGP issues, such as using BGP debugs, route tracing, and route validation to identify misconfigurations or network problems.",
                                
                                "12. BGP Case Studies and Real-World Examples": "Presents real-world BGP incidents and case studies, such as high-profile BGP hijacks or outages, and explains how these events impacted global routing and network stability."
                            },
                    jsonSnapshot: {"id": "seed_task_5", "name": "BGP Message Formats and Communication", "instruction": "Can you describe the various message formats that BGP uses for communication between routers?","instances": [    {        "input": "<noinput>",        "output": "BGP (Border Gateway Protocol) uses various message formats for effective communication between routers. These formats include the Open Message, which initiates connections and shares essential parameters. The Update Message conveys route changes, additions, or updates. Notification Messages signal errors, while Keepalive Messages maintain connections. These formats ensure routers establish, maintain, and update routing information, enabling reliable and efficient data forwarding across networks. BGP's message formats facilitate informed routing decisions and adaptability to network changes, contributing to stable and efficient internet routing."}],"is_classification": false},
                    },
                    {
                        id: 'bgp-knowledge-2',
                        title:'BGP Knowledge II',
                        fileUrl: '/finetuning-dataset/manual-seed-dataset/bgp-knowledge-2.jsonl',
                        promptUrl: '/finetuning-dataset/manual-seed-dataset/prompt_knowledge.txt',
                        fileCount: 36,
                        size: '49 KB',
                        fileType: 'jsonl',
                        promptType: 'txt',
                        description: "This the second knowledge dataset, which contains manually curated instruction-input-output pairs aimed at expanding the BGP (Border Gateway Protocol) knowledge base for advanced pre-trained language models like GPT. The dataset serves as a foundation for generating similar tasks that will help fine-tune models for complex BGP-related scenarios. By leveraging these initial seeds, the model can generate diverse and nuanced tasks related to BGP routing behavior, path selection, route stability, security issues, and real-time anomaly detection. The primary objective is to create a structured learning resource that helps the LLM (Large Language Model) understand BGP operations from fundamental principles to advanced case studies. This dataset is carefully designed to capture a wide range of BGP topics and provide both instructional value and real-world applicability in the context of network analysis, optimization, and security. \nThe inclusion of rules within the base prompt ensures consistency and relevance in the model-generated tasks, maintaining focus on BGP-specific domains. The generated tasks are expected to aid in research, network management, and anomaly detection tasks involving BGP routing data.",
                        categories: {
                                "1. BGP Fundamentals": "Covers the foundational principles of BGP, including how BGP functions as a path vector protocol and the basic mechanisms behind BGP route advertisements, decision processes, and convergence.",
                                
                                "2. BGP Security and Stability": "Focuses on the security challenges within BGP, such as prefix hijacking, route leaks, and methods to secure BGP routing, including RPKI (Resource Public Key Infrastructure) and filtering mechanisms.",
                                
                                "3. BGP Route Stability": "Explores the stability of BGP routes, path flapping, and the effect of route oscillation on global internet routing, including mitigation techniques such as route dampening.",
                                
                                "4. BGP Route Manipulation and Optimization": "Covers topics related to BGP route manipulation through policies and attributes such as local preference, MED, and AS-path prepending to optimize traffic flow and network performance.",
                                
                                "5. BGP Analysis and Anomaly Detection": "Focuses on detecting anomalies in BGP routing, such as route hijacks, leaks, and malicious activities, using tools and methods to analyze routing tables and BGP announcements.",
                                
                                "6. BGP Session Establishment and Maintenance": "Details the processes involved in establishing and maintaining BGP sessions between peers, including TCP connection setup, keepalive messages, and session termination.",
                                
                                "7. BGP Peer Grouping and Configuration": "Explains how BGP peer groups can be used to simplify configuration and enhance the scalability of routing policies, especially in large-scale networks.",
                                
                                "8. BGP Address Families": "Explores different BGP address families such as IPv4, IPv6, and VPNv4, and their respective roles in routing multiple protocol families within BGP.",
                                
                                "9. BGP Policies and Route Maps": "Covers the use of route maps, prefix lists, and filter policies to control the advertisement and acceptance of routes, and how these policies affect global routing decisions.",
                                
                                "10. BGP Multihoming and Load Balancing": "Examines how BGP is used for multihoming to improve redundancy and reliability in networks, including load balancing techniques across multiple ISPs.",
                                
                                "11. BGP Troubleshooting and Diagnostics": "Details tools and techniques for diagnosing and troubleshooting BGP issues, such as using BGP debugs, route tracing, and route validation to identify misconfigurations or network problems.",
                                
                                "12. BGP Case Studies and Real-World Examples": "Presents real-world BGP incidents and case studies, such as high-profile BGP hijacks or outages, and explains how these events impacted global routing and network stability."
                            },
                        jsonSnapshot: {"id": "seed_task_11", "name": "BGP Confederations and Scalability", "instruction": "Describe the concept of BGP Confederations, how they address BGP scalability issues in large networks, and their advantages over traditional route reflection.", "instances": [{"input": "Consider a large ISP with multiple internal BGP (iBGP) routers and the challenges of maintaining full-mesh peering.", "output": "BGP Confederations are a mechanism designed to address the scalability challenges associated with maintaining full-mesh iBGP peering in large networks. In a full-mesh iBGP setup, every router needs to establish peering with every other router, leading to a quadratic increase in the number of peering sessions as the network grows. Confederations address this by dividing an autonomous system (AS) into multiple sub-ASes or confederation members. These sub-ASes then peer among themselves using eBGP, while still appearing as a single AS to external peers. This approach significantly reduces the number of required peering sessions. Compared to traditional route reflection, confederations offer a more granular and flexible approach to BGP scalability. While route reflectors simplify iBGP topology by reducing the number of peering sessions, they can introduce suboptimal routing. Confederations, on the other hand, provide a more hierarchical structure, allowing for better path selection and more efficient routing decisions. In essence, BGP Confederations offer a scalable and efficient solution to the challenges of managing BGP in large, complex networks."}], "is_classification": false},
                    },
                    {
                        id: 'bgp-pybgpstream-base',
                        title:'PyBGPStream Base',
                        fileUrl: '/finetuning-dataset/manual-seed-dataset/bgp-pybgpstream-base.jsonl',
                        promptUrl: '/finetuning-dataset/manual-seed-dataset/prompt_pybgpstream.txt',
                        fileCount: 54,
                        size: '90 KB',
                        fileType: 'jsonl',
                        promptType: 'txt',
                        description: "This is a manually curated seed set that contains tasks specifically designed for BGP data collection and analysis using the PyBGPStream library. The tasks focus on demonstrating the essential utilization of PyBGPStream, guiding the LLM through the necessary syntax and workflow required to handle BGP data effectively. The dataset provides fundamental instruction-input-output pairs for LLMs to understand the operations of BGP routing, including real-time data processing, feature extraction, anomaly detection, and global routing behavior analysis. This foundational set serves to help the LLM generate additional tasks, expanding its capacity to work with BGP data and tools in diverse scenarios.",
                        jsonSnapshot: {"id": "seed_task_2", "name": "Investigating BGP Community Local Preference Variations", "instruction": "Investigate variations in local preference values associated with BGP communities using data from collector rrc03 on July 15, 2021, between 10:00 and 11:00.", "instances": [{"input": "Investigating BGP community local preference variations using data from collector rrc03 on July 15, 2021, between 10:00 and 11:00.", "output": "import pybgpstream\nfrom collections import defaultdict\n\n# Initialize BGP Stream\nstream = pybgpstream.BGPStream(\n    from_time=\"2021-07-15 10:00:00\", until_time=\"2021-07-15 11:00:00\",\n    project=\"ris\",\n    collectors=\"rrc03\",\n    record_type=\"updates\",\n    filter=\"ipversion 4\"\n)\n\n# Map of communities to local preference values\ncommunity_to_local_pref = defaultdict(list)\n\n# Loop through the stream records\nfor rec in stream.records():\n    for elem in rec:\n        if elem.type == \"A\":\n            communities = elem.fields.get('communities', None)\n            local_pref = elem.fields.get('local_pref', None)\n\n            if communities and local_pref:\n                for community in communities.split(\",\"):\n                    community_to_local_pref[community].append(int(local_pref))\n\n# Calculate average local preference for each community\nprint(\"Average Local Preference Values for Communities:\")\nfor community, local_prefs in community_to_local_pref.items():\n    avg_local_pref = sum(local_prefs) / len(local_prefs)\n    print(f\"{community}: {avg_local_pref}\")"}], "is_classification": false},
                    },
                    {
                        id: 'bgp-pybgpstream-real-case',
                        title:'PyBGPStream Real Cases',
                        fileUrl: '',
                        promptUrl: '/finetuning-dataset/manual-seed-dataset/prompt_pybgpstream.txt',
                        fileCount: 25,
                        size: '61 KB',
                        fileType: 'jsonl',
                        promptType: 'txt',
                        description: 'This dataset contains real BGP hijacking and anomaly cases, along with 25 hand-written PyBGPStream scripts. These scripts will help extract relevant features from the BGP data, conduct detailed analysis, and generate visualizations for comprehensive insight. The dataset is designed to facilitate understanding of BGP anomalies through practical and hands-on analysis. The inclusion of real cases of BGP anomalies is crucial for training and research purposes because it allows for a realistic understanding of how such events manifest in the real world. Synthetic data often lacks the complexity and nuances present in genuine incidents, making it insufficient for developing accurate detection and mitigation strategies. By using real BGP hijacking and anomaly cases, researchers and analysts can train models that are better equipped to recognize and respond to similar occurrences in live network environments. This leads to more robust anomaly detection systems, enhanced network security, and improved resilience against potential routing disruptions.', 
                        jsonSnapshot: {"id": "seed_task_0", "name": "Google May 2005 Outage", "instruction": "Visualize the BGP update timeline for the prefix 64.233.161.0/24 during the time window from May 7, 2005, 00:00:00 to May 7, 2005, 23:59:00. Use data from multiple RouteViews collectors, including route-views2, route-views3, route-views4, ris-ripe, bview, and rib, and collect BGP update records of type 'A' (Announcements) for this prefix. Plot the timeline to show how different Autonomous Systems (ASes) contributed to the announcements over time.", "instances": [{"input": "Time window: May 7, 2005, 00:00:00 to May 7, 2005, 23:59:00\nCollectors: route-views2, route-views3, route-views4, ris-ripe, bview, rib\nRecord Type: updates (Announcements)\nPrefix of Interest: 64.233.161.0/24", "output": "import pybgpstream\nimport matplotlib.pyplot as plt\nfrom datetime import datetime\n\n# Define the time window around the TTNet incident\nstart_time = \"2005-05-07 00:00:00\"\nend_time = \"2005-05-07 23:59:00\"\n\n# Initialize the BGPStream to use multiple RouteViews collectors\nstream = pybgpstream.BGPStream(\n    from_time=start_time,\n    until_time=end_time,\n    collectors=[\"route-views2\", \"route-views3\", \"route-views4\", \"ris-ripe\", \"bview\", \"rib\"],\n    record_type=\"updates\",\n)\n\nas_path_data = {}\ntimeline_data = {}\n\nfor elem in stream:\n    if elem.type == \"A\" and elem.fields[\"prefix\"] == \"64.233.161.0/24\":\n   as_path = elem.fields[\"as-path\"].split(\" \")\n   originating_as = as_path[-1]\n   timestamp = datetime.utcfromtimestamp(elem.time).strftime('%Y-%m-%d %H:%M:%S')\n\n   if originating_as not in as_path_data:\n  as_path_data[originating_as] = 1\n  timeline_data[originating_as] = [timestamp]\n   else:\n  as_path_data[originating_as] += 1\n  timeline_data[originating_as].append(timestamp)\n\n# Plotting the BGP Update Timeline\nplt.figure(figsize=(12, 6))\nfor as_num, timestamps in timeline_data.items():\n    plt.plot(timestamps, [as_num] * len(timestamps), marker='o', label=f\"AS{as_num}\")\n\nplt.xlabel('Timestamp')\nplt.ylabel('Autonomous System (AS)')\nplt.title('BGP Update Timeline for Prefix 64.233.161.0/24')\nplt.legend()\nplt.xticks(rotation=45)\nplt.tight_layout()\nplt.grid(axis='x')\nplt.show()"}], "is_classification": false},
                    },
                    {
                        id: 'bgp-pybgpstream-real-time',
                        title:'PyBGPStream Real-time Stream',
                        fileUrl: '/finetuning-dataset/manual-seed-dataset/bgp-pybgpstream-real-time.jsonl',
                        promptUrl: '/finetuning-dataset/manual-seed-dataset/prompt-pybgpstream-realtime.txt',
                        fileCount: 4,
                        size: '12 KB',
                        fileType: 'jsonl',
                        promptType: 'txt',
                        description: 'This dataset focuses on real-time BGP data analysis using PyBGPStream with the RIS Live collection. The scripts are designed to analyze specific prefix or ASN announcements, providing detailed insights into routing behavior and potential anomalies. By focusing on prefix and ASN-specific analysis, this dataset allows for a more granular understanding of routing changes, disruptions, and patterns within the BGP ecosystem. Such targeted analysis is crucial for identifying abnormal routing behavior, monitoring the stability of specific networks, and gaining insights into the propagation of route announcements across the internet. The dataset also includes visualization scripts to effectively illustrate the observed statistics.',
                        jsonSnapshot: {"id": "seed_task_0", "name": "AS18298 Real-Time BGP Data Analysis", "instruction": "Collect BGP update data for AS18298 over a specific collection period. Record prefix announcements and withdrawals during this period. Aggregate and visualize the collected data.", "instances": [{"input": "Collection Period: 72000 seconds\nTarget AS: 18298", "output": "import pybgpstream\nimport pandas as pd\nimport matplotlib.pyplot as plt\nimport time\n\ncollection_period = 72000\ntarget_as = \"18298\"\n\nprefix_announcements_df = pd.DataFrame(columns=['Time', 'Prefix', 'Count'])\nwithdrawals_df = pd.DataFrame(columns=['Time', 'Prefix', 'Count'])\n\nstream = pybgpstream.BGPStream(\n    project=\"ris-live\",\n    record_type=\"updates\",\n)\n\nstart_time = time.time()\n\nfor rec in stream.records():\n    if collection_period < time.time() - start_time:\n        print(\"Collection period ended. Processing data...\")\n        break\n\n    current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(rec.time))\n    for elem in rec:\n        as_path = elem.fields.get('as-path', '').split()\n        prefix = elem.fields['prefix']\n\n        if target_as in as_path:\n            if elem.type == 'A':\n                if prefix in prefix_announcements_df['Prefix'].values:\n                    prefix_announcements_df.loc[prefix_announcements_df['Prefix'] == prefix, 'Count'] += 1\n                else:\n                    new_row = pd.DataFrame({'Time': [current_time], 'Prefix': [elem.fields['prefix']], 'Count': [1]})\n                    prefix_announcements_df = pd.concat([prefix_announcements_df, new_row], ignore_index=True)\n            elif elem.type == 'W':\n                if prefix in withdrawals_df['Prefix'].values:\n                    withdrawals_df.loc[withdrawals_df['Prefix'] == prefix, 'Count'] += 1\n                else:\n                    new_row = pd.DataFrame({'Time': [current_time], 'Prefix': [elem.fields['prefix']], 'Count': [1]})\n                    withdrawals_df = pd.concat([withdrawals_df, new_row], ignore_index=True)\n\nprefix_announcements_df = prefix_announcements_df.groupby(['Prefix']).size().reset_index(name='Counts')\nwithdrawals_df = withdrawals_df.groupby(['Prefix']).size().reset_index(name='Counts')\n\ndef plot_data(df, title):\n    if not df.empty:\n        plt.figure(figsize=(10, 5))\n        plt.bar(df['Prefix'], df['Counts'], align='center')\n        plt.xticks(rotation=90)\n        plt.title(title)\n        plt.show()\n    else:\n        print(f\"No data to display for {title}\")\n\nplot_data(prefix_announcements_df, f\"Prefix Announcements for AS{target_as} (Collected Data)\")\nplot_data(withdrawals_df, f\"Withdrawals for AS{target_as} (Collected Data)\")"}], "is_classification": false},
                    },             
                ]
            },
            // other sections
    ],
    loading: false,
    error: null
};

const datasetsSlice = createSlice({
    name: 'datasets',
    initialState,
    reducers: {
        addDatasetToSection: (state, action) => {
            const { sectionTitle, newDataset } = action.payload;
            const section = state.allDatasets.find(section => section.title === sectionTitle);
            if (section) {
                section.datasets.push(newDataset);
            }
        },        
        removeDatasetFromSection: (state, action) => {
            const { sectionTitle, datasetId } = action.payload;
            const section = state.allDatasets.find(section => section.title === sectionTitle);
            if (section) {
                section.datasets = section.datasets.filter(dataset => dataset.id !== datasetId);
            }
        },        
        updateDatasetInSection: (state, action) => {
            const { sectionTitle, updatedDataset } = action.payload;
            const section = state.allDatasets.find(section => section.title === sectionTitle);
            if (section) {
                const index = section.datasets.findIndex(dataset => dataset.id === updatedDataset.id);
                if (index !== -1) {
                    section.datasets[index] = updatedDataset;
                }
            }
        },        
        // Additional reducers for adding, removing, or updating whole sections could be added here
    }
});

export const { addDatasetToSection, removeDatasetFromSection, updateDatasetInSection } = datasetsSlice.actions;
export default datasetsSlice.reducer;

// Initial State: Defined starting state for the slice.
// Reducers: Functions defining how state changes in response to actions. These update the state based on the type of action and the payload provided.
// Action Creators: Automatically generated functions (addDataset, removeDataset, updateDataset) that you can call to create action objects to dispatch to the store.