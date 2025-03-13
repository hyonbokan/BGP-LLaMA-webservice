import React from "react";
import { Box, Grid, Card, CardContent, Typography, Button } from "@mui/material";
import { Link } from "react-router-dom";

const BottomCards = ({ cardData }) => {
  return (
    <Box sx={{ py: 4 }}>
      <Grid container spacing={4}>
        {cardData.map((card, index) => {
          const isExternal = card.link && card.link.startsWith("http");
          return (
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
                  {card.link ? (
                    isExternal ? (
                      <Button
                        variant="outlined"
                        color="inherit"
                        size="small"
                        sx={{ textTransform: "none", fontFamily: "Roboto Mono" }}
                        href={card.link}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {card.buttonText}
                      </Button>
                    ) : (
                      <Button
                        variant="outlined"
                        color="inherit"
                        size="small"
                        sx={{ textTransform: "none", fontFamily: "Roboto Mono" }}
                        component={Link}
                        to={card.link}
                      >
                        {card.buttonText}
                      </Button>
                    )
                  ) : (
                    <Button
                      variant="outlined"
                      color="inherit"
                      size="small"
                      sx={{ textTransform: "none", fontFamily: "Roboto Mono" }}
                      disabled
                    >
                      {card.buttonText}
                    </Button>
                  )}
                </Box>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
};

export default BottomCards;
