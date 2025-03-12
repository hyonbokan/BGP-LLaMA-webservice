const capabilitiesData = [
    {
      category: "BGP Routing and Prefix Analysis",
      subcapabilities: [
        {
          title: "Subprefix Deaggregation Analysis",
          description:
            "Examines relationships between subprefixes and their origin ASes to identify deaggregation patterns.",
        },
        {
          title: "Time-Series Trend Analysis",
          description:
            "Analyzes announcements and withdrawals over defined time buckets (5 minutes, 1 hour) to spot trends.",
        },
        {
          title: "Origin AS Change Tracking",
          description:
            "Monitors changes in the origin AS of prefixes to reveal shifts in routing behavior.",
        },
        {
          title: "Top Origin AS by Prefix",
          description:
            "Counts unique prefixes per origin AS and calculates aggregations (max, average) for comparative analysis.",
        },
        {
          title: "AS Path Length Comparison",
          description:
            "Compares AS path lengths between IPv4 and IPv6 routes, providing insight into path distribution.",
        },
        {
          title: "Overlapping Prefix Detection",
          description:
            "Identifies cases where prefix lengths overlap and tracks the associated origin ASNs.",
        },
      ],
    },
    {
      category: "AS Path and Policy Analysis",
      subcapabilities: [
        {
          title: "AS Path Change Detection",
          description:
            "Detects modifications in AS paths for prefixes, highlighting routing adjustments and changes.",
        },
        {
          title: "AS Path Prepending Analysis",
          description:
            "Assesses the frequency and occurrence of AS path prepending to infer traffic engineering practices.",
        },
        {
          title: "Longest AS Paths",
          description:
            "Analyzes the distribution of AS path lengths and identifies extreme values in both IPv4 and IPv6.",
        },
        {
          title: "AS Looping Detection",
          description:
            "Detects recurring AS patterns indicating potential loops or misconfigurations at the prefix level.",
        },
        {
          title: "MED Variation Analysis",
          description:
            "Examines variations in the Multi-Exit Discriminator (MED) values, including min, max, and average.",
        },
        {
          title: "ATOMIC_AGGREGATE Detection",
          description:
            "Checks for the presence of the ATOMIC_AGGREGATE flag in BGP updates to detect routing aggregation anomalies.",
        },
      ],
    },
    {
      category: "BGP Anomaly and Security Detection",
      subcapabilities: [
        {
          title: "MOAS & Hijack Cross-Check",
          description:
            "Identifies multiple origin AS announcements and suspicious indicators for potential hijacks.",
        },
        {
          title: "Well-Known BGP Community Analysis",
          description:
            "Analyzes well-known BGP communities in updates to provide insights at the prefix level.",
        },
        {
          title: "Route Flapping Detection",
          description:
            "Monitors the frequency of route flaps over short time buckets to detect unstable routes.",
        },
        {
          title: "Update Storm Detection",
          description:
            "Identifies periods of excessively high update frequencies that exceed defined thresholds.",
        },
        {
          title: "RPKI Invalid Announcements",
          description:
            "Checks for announcements with invalid RPKI statuses, highlighting potential security issues.",
        },
        {
          title: "Route Leak Detection",
          description:
            "Verifies AS path consistency and policy adherence to detect potential route leaks.",
        },
      ],
    },
    {
      category: "AS Relationship and Topology Analysis",
      subcapabilities: [
        {
          title: "AS Adjacency Analysis",
          description:
            "Examines neighbor relationships in AS paths and counts occurrences to reveal network topology.",
        },
        {
          title: "AS Relationship Tracking",
          description:
            "Monitors changes in transit relationships over time to identify shifts in AS connectivity.",
        },
        {
          title: "Community-based Traffic Engineering",
          description:
            "Analyzes BGP community attributes to infer traffic engineering decisions and routing policies.",
        },
        {
          title: "Extended Community Analysis",
          description:
            "Provides detailed insights into extended communities and their impact on prefix-level routing.",
        },
      ],
    },
  ];

  export default capabilitiesData;