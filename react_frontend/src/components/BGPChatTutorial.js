import React from 'react';
import { Typography, Box } from '@mui/material';

const BGPChatTutorial = () => (
  <Box sx={{ p: 3 }}>
    <Typography variant="h5" gutterBottom>
      Welcome to BGP-LLaMA Chat!
    </Typography>

    <Typography variant="body1" paragraph>
      Please note that the system is currently in its early stages, and user commands must be formatted correctly for optimal performance.
    </Typography>

    <Typography variant="h6" gutterBottom>
      1. BGP Data Collection
    </Typography>
    <Typography variant="body1" paragraph>
      BGP data collection is the first step for data analysis.
    </Typography>
    <Typography variant="body1" paragraph>
      To initiate a data collection, include the command <b>"collect"</b> and specify the type of collection:
    </Typography>

    <Typography variant="body1" paragraph>
      - For <b>historical data</b>, please specify the timeline in the format <i>yy-mm-dd hh:mm:ss</i>.
    </Typography>
    <Typography variant="body2" paragraph>
      Example: <i>Collect BGP data for AS15169 from 2017-08-25 03:00:00 to 2017-08-25 04:00:00.</i>
    </Typography>

    <Typography variant="body1" paragraph>
      - For <b>real-time data</b>, use the term <i>"real-time"</i> along with the duration (e.g., minutes, hours, days).
    </Typography>
    <Typography variant="body2" paragraph>
      Example: <i>Collect real-time BGP data for AS3356 for 30 minutes.</i>
    </Typography>

    <Typography variant="h6" gutterBottom>
      2. Default BGP Dataset
    </Typography>
    <Typography variant="body1" paragraph>
      By default, the system has access to data from Facebook AS32934 between <b>2021-10-04 07:00:00</b> and <b>2021-10-05 22:00:00</b>, which covers a notable BGP anomaly event.
    </Typography>

    <Typography variant="h6" gutterBottom>
      3. Data Insights & Anomaly Detection
    </Typography>
    <Typography variant="body1" paragraph>
      After data collection, you can query the system to gain insights or detect anomalies in the collected BGP data.
    </Typography>
  </Box>
);

export default BGPChatTutorial;
