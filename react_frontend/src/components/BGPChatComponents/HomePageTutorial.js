import React, { useState } from "react";
import {
  Grid,
  Box,
  Typography,
  Card,
  CardMedia,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Button,
  Collapse,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import capabilitiesData from "../../utils/capabilities";

const HomePageTutorial = () => {
  const [expandedIndex, setExpandedIndex] = useState(-1);
  const [showExamples, setShowExamples] = useState(false);

  const handleAccordionChange = (index) => (event, isExpanded) => {
    setExpandedIndex(isExpanded ? index : -1);
  };

  const handleToggleExamples = () => {
    setShowExamples((prev) => !prev);
  };

  return (
    <Box sx={{ backgroundColor: "white", pt: 8, pb: 4 }}>
      {/* 1) Overview + Video Row */}
      <Grid container spacing={4} sx={{ px: 2 }}>
        {/* Left Column: Overview Text */}
        <Grid item xs={12} md={6}>
          <Typography variant="h5" gutterBottom sx={{ fontWeight: "bold" }}>
            Overview of BGP-LLaMA
          </Typography>
          <Typography variant="body1" paragraph>
            BGP-LLaMA offers two options for performance comparison:
            <br />
            <b>- Prompt Engineered GPT-4o-mini</b>
            <br />
            <b>- Finetuned LLaMA 3.1 8B Model (BGP-LLaMA)</b>
            <br />
            Choose the mode that best suits your analysis needs based on speed and accuracy.
          </Typography>

          <Typography variant="body1" paragraph>
            <b>BGP-LLaMA web application</b> is an open-source system designed by leveraging an 
            instruction fine-tuned LLaMA 2 13B model. The system automates the generation of code 
            scripts for BGP data collection, processes vast volumes of routing data, and performs 
            both historical and real-time analysis.
          </Typography>

          <Typography variant="body1" paragraph>
            BGP-LLaMA streamlines traditionally manual processes, such as writing custom code for 
            data extraction, parsing complex routing information, and detecting network anomalies, 
            significantly reducing the time and expertise required to analyze BGP data. It also 
            handles large-scale, high-frequency BGP updates across multiple vantage points while 
            delivering concise, natural language reports—providing network engineers with 
            actionable insights in a clear, interpretable format.
          </Typography>
        </Grid>

        {/* Right Column: Demo GIF */}
        <Grid item xs={12} md={6}>
          <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100%" }}>
            <Card
              sx={{
                width: "100%",
                boxShadow: 3,
                borderRadius: 2,
              }}
            >
              <CardMedia
                component="img"
                height="315"
                image={`${process.env.PUBLIC_URL}/assets/google_leak_format.gif`}
                title="BGP-LLaMA Demo"
                sx={{ objectFit: "cover" }}
              />
            </Card>
          </Box>
        </Grid>
      </Grid>

      {/* 2) Key Capabilities (Accordion) */}
      <Box sx={{ mt: 6, px: 2 }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: "bold" }}>
          Key Capabilities
        </Typography>
        <Typography variant="body1" paragraph>
          Click on each category to view the subcapabilities and learn more about the analysis tasks.
        </Typography>

        {capabilitiesData.map((capability, index) => (
          <Accordion
            key={index}
            expanded={expandedIndex === index}
            onChange={handleAccordionChange(index)}
            sx={{
              border: "1px solid #E2E8F0",
              borderRadius: "8px",
              boxShadow: "none",
              mb: 2,
            }}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ backgroundColor: "#EDF2F7" }}>
              <Typography variant="h6" color="primary">
                {capability.category}
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <List>
                {capability.subcapabilities.map((sub, idx) => (
                  <ListItem key={idx} disablePadding>
                    <ListItemText
                      primary={
                        <Typography variant="subtitle1">
                          <b>{sub.title}</b>
                        </Typography>
                      }
                      secondary={
                        <Typography variant="body2">{sub.description}</Typography>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>

      {/* 3) Additional Info & Example Queries */}
      <Box sx={{ mt: 6, px: 2 }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: "bold" }}>
          Additional Information & Testing
        </Typography>
        <Typography variant="body1" paragraph>
          To reduce data processing overhead, BGP update messages from the RIPE RIS rrc00 collector for the entire
          month of October 2024 have been pre-processed and stored. For optimal performance, all queries should be
          limited to this time range.
        </Typography>

        <Button
          variant="outlined"
          color="primary"
          onClick={handleToggleExamples}
          sx={{ mt: 2, textTransform: "none", fontFamily: "Roboto Mono" }}
        >
          {showExamples ? "Hide Example Queries" : "Show Example Queries"}
        </Button>

        <Collapse in={showExamples}>
          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            <b>Example Analysis Queries</b>
          </Typography>
          <Typography variant="body1" paragraph>
            <b>Prefix and Origin Analysis:</b> Summarize unique prefixes and origin ASes for AS4766 between Oct 28 13:00
            and 13:15, 2024.
          </Typography>
          <Typography variant="body1" paragraph>
            <b>AS Path Analysis:</b> Provide statistics on AS path lengths (min, max, median) for prefixes associated
            with AS4766 over the same period.
          </Typography>
          <Typography variant="body1" paragraph>
            Start with these examples or create your own queries to explore the full capabilities of BGP-LLaMA.
          </Typography>
        </Collapse>
      </Box>
    </Box>
  );
};

export default HomePageTutorial;