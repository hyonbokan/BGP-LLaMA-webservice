"use client";
import React, { useState } from "react";
import { Card, CardContent, Typography, Button, Box } from "@mui/material";

const WhatsNewCard = ({ update, buttons }) => {
  const [expanded, setExpanded] = useState(false);
  const MAX_LENGTH = 200;
  // Show toggle only if the detail text is longer than MAX_LENGTH characters.
  const showToggle = update.detail.length > MAX_LENGTH;

  const toggleExpanded = () => setExpanded((prev) => !prev);

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
            variant="body1"
            sx={{
              mb: 1,
              whiteSpace: "pre-line", // respects newline characters in update.detail
              // When not expanded, limit display to 5 lines
              ...(!expanded && {
                display: "-webkit-box",
                WebkitLineClamp: 5,
                WebkitBoxOrient: "vertical",
                overflow: "hidden",
              }),
              lineHeight: 1.6,
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
        {/* Footer: The update date is always anchored at the bottom */}
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