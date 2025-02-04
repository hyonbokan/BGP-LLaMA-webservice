import { Box, Typography, Card, CardContent } from '@mui/material';

const BGPChatTutorial = () => (
  <Box sx={{ p: 3 }}>
    <Typography variant="h5" gutterBottom>
      Welcome to BGP-LLaMA Chat!
    </Typography>
    <Box sx={{ mt: 2 }}>
      {/* Section: Key Information */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6">Key Information</Typography>
          <Typography variant="body1" gutterBottom>
            To reduce data processing overhead, we have pre-processed and stored BGP update messages from the RIPE RIS rrc00 collector for the entire month of October 2024. All queries should be limited to this time range for optimal performance.
          </Typography>
        </CardContent>
      </Card>

      {/* Section: Supported Analysis Queries */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6">Example of Analysis Queries</Typography>
          <Typography variant="body1" sx={{ mb: 1 }}>
            Below are some example queries you can use to interact with BGP-LLaMA:
          </Typography>

          {/* Query: Prefix and Origin Analysis */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle1">Prefix and Origin Analysis</Typography>
            <Typography
              variant="body2"
              sx={{
                bgcolor: '#f4f4f4',
                p: 2,
                borderRadius: 1,
                fontFamily: 'monospace',
              }}
            >
              Provide a summary of unique prefixes and origin ASes associated
              with AS4766 from Oct 28 13:00 to 13:15, 2024. Track the count of
              unique prefixes and changes in origin ASes, if any.
            </Typography>
          </Box>

          {/* Query: AS Path Analysis */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle1">AS Path Analysis</Typography>
            <Typography
              variant="body2"
              sx={{
                bgcolor: '#f4f4f4',
                p: 2,
                borderRadius: 1,
                fontFamily: 'monospace',
              }}
            >
              Summarize the AS paths for each prefix associated with ASN AS4766
              over the period Oct 28 13:00 to 13:15, 2024. Provide minimum,
              maximum, and median AS path lengths and highlight any significant
              path changes observed in BGP updates.
            </Typography>
          </Box>

          {/* Query: MED and Community Tag Analysis */}
          <Box>
            <Typography variant="subtitle1">
              MED and Community Tag Analysis
            </Typography>
            <Typography
              variant="body2"
              sx={{
                bgcolor: '#f4f4f4',
                p: 2,
                borderRadius: 1,
                fontFamily: 'monospace',
              }}
            >
              Analyze the range of MED values and the most common community
              tags associated with BGP update messages for ASN AS4766 from Oct
              28 13:00 to 13:15, 2024. Provide a summary of average MED values
              and frequently observed community tags.
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Section: Testing Queries */}
      <Card>
        <CardContent>
          <Typography variant="h6">Testing Queries</Typography>
          <Typography variant="body1">
            Start with the example queries above or create your own to explore
            the full capabilities of BGP-LLaMA.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  </Box>
);

export default BGPChatTutorial;