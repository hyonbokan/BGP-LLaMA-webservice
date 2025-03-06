import React from 'react';
import { Grid, Typography, Card, CardMedia } from '@mui/material';

const HomePageTutorial = () => (
  <Grid container spacing={4} sx={{ py: 8 }}>
    <Grid item xs={12} md={6}>
      <Typography variant='h5' gutterBottom>
        <b>Overview of BGP-LLaMA</b>
      </Typography>

      <Typography variant="body1" paragraph>
        BGP-LLaMA is an open-source, instruction fine-tuned version of the LLaMA model designed to automate and assist with BGP data collection, processing, and analysis.
      </Typography>

      <Typography variant="h6" gutterBottom>
        <b>Key Capabilities of BGP-LLaMA:</b>
      </Typography>

      <Typography variant="body1" paragraph>
        <b>1. Monitor Current Trends:</b> Tracks routing trends over various time periods (5 minutes, 1 hour, 1 day, 1 week) from multiple vantage points, offering insights into AS behavior and dynamics.
      </Typography>

      <Typography variant="body1" paragraph>
        <b>2. AS Path Change Updates:</b> Monitors and reports changes in AS paths to understand routing dynamics and path stability. It detects AS path changes and aggregates updates per peer ASN.
      </Typography>

      <Typography variant="body1" paragraph>
        <b>3. Prefix Analysis:</b> Tracks announcements and withdrawals of BGP prefixes, collecting metrics such as prefix lengths, MED, and local preferences for a detailed analysis of prefix behavior.
      </Typography>

      <Typography variant="body1" paragraph>
        <b>4. Anomaly Detection:</b> Identifies BGP hijacks, route leaks, and routing loops to secure the network. Future enhancements include advanced detection mechanisms and real-time alerts.
      </Typography>

      <Typography variant="body1" paragraph>
        <b>5. BGP Hijacking Detection:</b> Detects hijacking anomalies, logging unexpected ASNs involved in hijacking events. Future plans include more sophisticated hijacking detection and alert systems.
      </Typography>

      <Typography variant="body1" paragraph>
        <b>6. Routing Policy Analysis:</b> Summarizes key routing policies such as local preferences, MED, and BGP communities to generate insightful reports on routing behavior and policy impact.
      </Typography>

      <Typography variant="h6" gutterBottom>
        <b>BGP Data Collection</b>
      </Typography>

      <Typography variant="body1" paragraph>
        To initiate a data collection, include the command <b>"collect"</b> and specify the type of collection:
      </Typography>
      <Typography variant="body1" paragraph>
      - For historical data, use the format <i>yy-mm-dd hh:mm:ss</i>.
      </Typography>
      <Typography variant="body1" paragraph>
      - For real-time data, specify the duration (e.g., minutes, hours, days).
      </Typography>

      <Typography variant="h6" gutterBottom>
        <b>Default BGP Dataset</b>
      </Typography>

      <Typography variant="body1" paragraph>
        By default, the system has access to data from Google AS15169 between <b>2017-08-25 00:00:00</b> and <b>2017-08-25 07:00:00</b>, which covers a notable BGP anomaly event.
      </Typography>

      <Typography variant="h6" gutterBottom>
        <b>Data Insights & Anomaly Detection</b>
      </Typography>

      <Typography variant="body1" paragraph>
        After data collection, you can query the system to gain insights or detect anomalies in the collected BGP data.
      </Typography>
    </Grid>

    <Grid item xs={12} md={6}>
      <Card>
        <CardMedia 
          component="img"
          height="315"
          image={`${process.env.PUBLIC_URL}/assets/google_leak_format.gif`}
          title="BGP-LLaMA Demo"
        />
      </Card>
    </Grid>
  </Grid>
);

export default HomePageTutorial;
