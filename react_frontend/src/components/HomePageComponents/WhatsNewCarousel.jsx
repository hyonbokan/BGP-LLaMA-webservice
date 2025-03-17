"use client";
import React, { useState } from "react";
import { Box, Typography, Container } from "@mui/material";
import Slider from "react-slick";
import "slick-carousel/slick/slick.css"; 
import "slick-carousel/slick/slick-theme.css";
import whatsNewData from "../../utils/whatsNewData";
import WhatsNewCard from "./WhatsNewCard";

import ArrowForwardIosIcon from "@mui/icons-material/ArrowForwardIos";
import ArrowBackIosIcon from "@mui/icons-material/ArrowBackIos";

// Custom Next Arrow positioned at the right edge
function NextArrow(props) {
  const { onClick } = props;
  return (
    <Box
      onClick={onClick}
      sx={{
        position: "absolute",
        top: "50%",
        right: "0px",
        transform: "translateY(-50%)",
        zIndex: 3,
        width: 50,
        height: 50,
        borderRadius: "50%",
        backgroundColor: "#fff",
        boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
        color: "#318CE7",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        fontSize: "1.8rem",
      }}
    >
      <ArrowForwardIosIcon fontSize="inherit" />
    </Box>
  );
}

// Custom Prev Arrow positioned at the left edge
function PrevArrow(props) {
  const { onClick } = props;
  return (
    <Box
      onClick={onClick}
      sx={{
        position: "absolute",
        top: "50%",
        left: "0px",
        transform: "translateY(-50%)",
        zIndex: 3,
        width: 50,
        height: 50,
        borderRadius: "50%",
        backgroundColor: "#fff",
        boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
        color: "#318CE7",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        fontSize: "1.8rem",
      }}
    >
      <ArrowBackIosIcon fontSize="inherit" />
    </Box>
  );
}

const WhatsNewCarousel = () => {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleCardToggle = () => {
    // Force a re-render of the slider when a card toggles
    setRefreshKey((prev) => prev + 1);
  };

  const settings = {
    dots: true,
    infinite: true,
    arrows: true,
    nextArrow: <NextArrow />,
    prevArrow: <PrevArrow />,
    speed: 500,
    slidesToShow: 3,
    slidesToScroll: 1,
    adaptiveHeight: true,
    responsive: [
      { breakpoint: 960, settings: { slidesToShow: 2 } },
      { breakpoint: 600, settings: { slidesToShow: 1 } },
    ],
  };

  return (
    <Box
      sx={{
        width: "100%",
        backgroundColor: "#F7FAFC",
        py: 4,
        mb: 4,
        "& .slick-list": { overflow: "visible" },
      }}
    >
      <Container>
        <Typography variant="h5" align="center" sx={{ fontWeight: "bold", mb: 3 }}>
          What's New
        </Typography>
      </Container>
      <Slider key={refreshKey} {...settings}>
        {whatsNewData.slice(0, 3).map((update, index) => (
          <Box key={index} sx={{ px: 2 }}>
            <WhatsNewCard update={update} onToggle={handleCardToggle} />
          </Box>
        ))}
      </Slider>
    </Box>
  );
};

export default WhatsNewCarousel;