import React, { useState } from "react";
import { Card, CardContent, Typography, Button, Box } from "@mui/material";

const WhatsNewCard = ({ update, buttons }) => {
  const [expanded, setExpanded] = useState(false);
  
  const toggleExpanded = () => setExpanded(prev => !prev);

  // Determine whether to show the toggle button based on the text length.
  const showToggle = update.detail.length > 150;

  return (
    <Card
      sx={{
        borderRadius: "16px",
        boxShadow: 3,
        display: "flex",
        flexDirection: "column",
        minHeight: 320,
      }}
    >
      <CardContent sx={{ display: "flex", flexDirection: "column", flexGrow: 1 }}>
        <Box sx={{ flexGrow: 1 }}>
          <Typography
            variant="h6"
            sx={{ fontFamily: "Roboto Mono", fontWeight: "bold", mb: 1 }}
          >
            {update.title}
          </Typography>
          <Typography
            variant="body2"
            sx={{
              mb: 1,
              ...( !expanded && {
                display: "-webkit-box",
                WebkitLineClamp: 5, // show 5 lines when collapsed
                WebkitBoxOrient: "vertical",
                overflow: "hidden",
              }),
            }}
          >
            {update.detail}
          </Typography>
          {showToggle && (
            <Box sx={{ textAlign: "right", mb: 1 }}>
              <Button
                size="small"
                onClick={toggleExpanded}
                sx={{ textTransform: "none", fontFamily: "Roboto Mono" }}
              >
                {expanded ? "Read Less" : "Read More"}
              </Button>
            </Box>
          )}
          {buttons && (
            <Box sx={{ mt: 2, display: "flex", gap: 1 }}>
              {buttons.map((btn, i) => (
                <Button
                  key={i}
                  variant={btn.variant || "outlined"}
                  color={btn.color || "inherit"}
                  size="small"
                  onClick={btn.onClick}
                  sx={{ textTransform: "none", fontFamily: "Roboto Mono" }}
                >
                  {btn.text}
                </Button>
              ))}
            </Box>
          )}
        </Box>
        {/* Footer: Date is always at the bottom */}
        <Box sx={{ mt: "auto" }}>
          <Typography variant="caption" color="text.secondary">
            {update.date}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default WhatsNewCard;
