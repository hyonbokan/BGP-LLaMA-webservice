import React from "react";
import Navbar from "../components/PageComponents/Navbar";
import Footer from "../components/PageComponents/Footer";
import HomePageTutorial from "../components/BGPChatComponents/HomePageTutorial";
import { Container, Typography, Button, Grid, Card, CardContent, Box } from "@mui/material";
import { Link } from "react-router-dom";
import homePageCardData from "../utils/homePageCardData";

const HomePage = () => {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        backgroundColor: "white",
      }}
    >
      <Navbar />
      <Container
        component="main"
        sx={{
          flexGrow: 1,
          py: 4,
          px: { xs: 2, md: 4 },
        }}
      >
        {/* Hero Section */}
        <Box sx={{ py: 8, textAlign: "center" }}>
          <Typography
            variant="h3"
            gutterBottom
            sx={{
              fontFamily: "Courier New, monospace",
              fontWeight: 550,
            }}
          >
            Welcome to BGP-LLaMA{" "}
            <Typography component="span" variant="h3" color="primary" sx={{fontWeight: 550}}>
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
        </Box>

        {/* Tutorial Section (Reorganized for modern look) */}
        <HomePageTutorial />

        {/* Bottom Cards Section */}
        <Box sx={{ py: 4 }}>
          <Grid container spacing={4}>
            {homePageCardData.map((card, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card
                  sx={{
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                    background: card.gradient,
                    color: "black",
                    borderRadius: "16px",
                    boxShadow: 3,
                  }}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Typography
                      gutterBottom
                      variant="h5"
                      component="h2"
                      sx={{ fontFamily: "Roboto Mono", fontWeight: "bold" }}
                    >
                      {card.title}
                    </Typography>
                    <Typography variant="body1" sx={{ fontFamily: "Roboto", lineHeight: 1.6 }}>
                      {card.description}
                    </Typography>
                  </CardContent>
                  <Box sx={{ p: 2, textAlign: "center" }}>
                    <Button
                      variant="outlined"
                      color="inherit"
                      size="small"
                      sx={{ textTransform: "none", fontFamily: "Roboto Mono" }}
                    >
                      {card.buttonText}
                    </Button>
                  </Box>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      </Container>
      <Footer />
    </Box>
  );
};

export default HomePage;