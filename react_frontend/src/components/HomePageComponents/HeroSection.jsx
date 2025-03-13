import React from "react";
import { Box, Typography, Button, Container } from "@mui/material";
import { Link } from "react-router-dom";

const HeroSection = () => {
  return (
    <Box sx={{ py: 8, textAlign: "center", backgroundColor: "white" }}>
      <Container>
        <Typography
          variant="h3"
          gutterBottom
          sx={{
            fontFamily: "Courier New, monospace",
            fontWeight: 550,
          }}
        >
          Welcome to BGP-LLaMA{" "}
          <Typography component="span" variant="h3" color="primary" sx={{ fontWeight: 550 }}>
            1.0
          </Typography>
        </Typography>
        <Typography
          variant="h6"
          paragraph
          sx={{
            fontFamily: "Courier New, monospace",
            fontWeight: 550,
            color: "text.secondary",
            maxWidth: 800,
            margin: "0 auto",
          }}
        >
          BGP-LLaMA is an instruction-finetuned, open-source LLM engineered for automating and
          scaling BGP routing data analysis, providing natural language reports and actionable
          insights.
        </Typography>
        <Button
          variant="contained"
          color="primary"
          component={Link}
          to="/bgp_chat"
          sx={{
            textTransform: "none",
            fontFamily: "Roboto Mono",
            mt: 2,
          }}
        >
          Get Started
        </Button>
      </Container>
    </Box>
  );
};

export default HeroSection;
