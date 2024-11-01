import { Box, Typography } from '@mui/material';

const GPTChatTutorial = () => (
  <Box sx={{ p: 3 }}>
    <Typography variant="h5" gutterBottom>
      Welcome to BGP with GPT 4o mini
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
      - For <b>historical data</b>, please specify the timeline in the format <i>yy-mm-dd hh:mm:ss</i>, include the specific collector (e.g., <i>route-views.amsix</i> or <i>rrc02</i>), and it is recommended to include both the target ASN and prefixes for comprehensive analysis.
    </Typography>
    <Typography variant="body2" paragraph>
      Example: <i>Collect and analyze data for AS32934 from 2021-10-04 07:00:00 to 2021-10-04 07:30:00 using collector route-views.amsix for prefixes 129.134.30.0/24 and 129.134.30.0/23.</i>
    </Typography>

    <Typography variant="body1" paragraph>
      - For <b>real-time data</b>, use the term <i>"real-time"</i> along with the duration (e.g., minutes), specify target ASN and optionally prefixes. Ensure that the duration does not exceed 30 minutes.
    </Typography>
    <Typography variant="body2" paragraph>
      Example: <i>Collect real-time BGP data for AS3356 for 30 minutes.</i>
    </Typography>

    <Typography variant="h6" gutterBottom>
      2. Data Insights & Anomaly Detection
    </Typography>
    <Typography variant="body1" paragraph>
      After data collection, you can query the system to gain insights or detect anomalies in the collected BGP data.
    </Typography>
  </Box>
);

export default GPTChatTutorial;