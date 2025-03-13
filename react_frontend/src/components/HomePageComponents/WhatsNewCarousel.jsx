"use client";
import React from "react";
import { Box, Typography, Container } from "@mui/material";
import Slider from "react-slick";
import "slick-carousel/slick/slick.css"; 
import "slick-carousel/slick/slick-theme.css";
import whatsNewData from "../../utils/whatsNewData";
import WhatsNewCard from "./WhatsNewCard"

import ArrowForwardIosIcon from "@mui/icons-material/ArrowForwardIos";
import ArrowBackIosIcon from "@mui/icons-material/ArrowBackIos";


function NextArrow(props) {
  const { onClick } = props;
  return (
    <Box
      onClick={onClick}
      sx={{
        position: "absolute",
        top: "50%",
        right: "25px",
        transform: "translateY(-50%)",
        zIndex: 3,
        width: 40,
        height: 40,
        borderRadius: "50%",
        backgroundColor: "#fff",
        boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
        color: "#318CE7",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        fontSize: "1.5rem",
      }}
    >
      <ArrowForwardIosIcon fontSize="small" />
    </Box>
  );
}

function PrevArrow(props) {
  const { onClick } = props;
  return (
    <Box
      onClick={onClick}
      sx={{
        position: "absolute",
        top: "50%",
        left: "25px",
        transform: "translateY(-50%)",
        zIndex: 3,
        width: 40,
        height: 40,
        borderRadius: "50%",
        backgroundColor: "#fff",
        boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
        color: "#318CE7",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        fontSize: "1.5rem",
      }}
    >
      <ArrowBackIosIcon fontSize="small" />
    </Box>
  );
}

const WhatsNewCarousel = () => {
  const settings = {
    dots: true,
    infinite: true,
    arrows: true,
    nextArrow: <NextArrow />,
    prevArrow: <PrevArrow />,
    speed: 500,
    slidesToShow: 3,
    slidesToScroll: 1,
    responsive: [
      { breakpoint: 960, settings: { slidesToShow: 2 } },
      { breakpoint: 600, settings: { slidesToShow: 1 } },
    ],
  };

  return (
    <Box sx={{ width: "100%", backgroundColor: "#F7FAFC", py: 4 }}>
      <Container
        sx={{
          // overflow is visible for the arrow icons & card bottoms
          "& .slick-list": { overflow: "visible" },
        }}
      >
        <Typography variant="h5" align="center" sx={{ fontWeight: "bold", mb: 3 }}>
          What's New
        </Typography>
        <Slider {...settings}>
          {whatsNewData.map((update, index) => (
            <Box key={index} sx={{ px: 2 }}>
              <WhatsNewCard update={update} />
            </Box>
          ))}
        </Slider>
      </Container>
    </Box>
  );
};

export default WhatsNewCarousel;