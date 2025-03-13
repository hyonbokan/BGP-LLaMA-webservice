import React from "react";
import Navbar from "../components/PageComponents/Navbar";
import Footer from "../components/PageComponents/Footer";
import HeroSection from "../components/HomePageComponents/HeroSection";
import WhatsNewCarousel from "../components/HomePageComponents/WhatsNewCarousel";
import HomePageTutorial from "../components/HomePageComponents/HomePageTutorial";
import BottomCards from "../components/HomePageComponents/BottomCards";
import { Container, Box } from "@mui/material";
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
      {/* Global Navbar */}
      <Navbar />

      {/* Hero Section */}
      <HeroSection />

      {/* What's New Carousel (full-width with internal container) */}
      <WhatsNewCarousel />

      {/* Tutorial Section */}
      <Container>
        <HomePageTutorial />
      </Container>

      {/* Bottom Cards Section */}
      <Container>
        <BottomCards cardData={homePageCardData} />
      </Container>

      {/* Global Footer */}
      <Footer />
    </Box>
  );
};

export default HomePage;