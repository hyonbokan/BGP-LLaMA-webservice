import React from 'react';
import { ListItem, Card, CardContent, Typography, Box } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css'; 

const ChatMessage = ({ message }) => (
  <ListItem
    alignItems="flex-start"
    sx={{
      display: 'flex',
      flexDirection: message.sender === "user" ? 'row-reverse' : 'row',
      padding: '8px 0', // Add vertical padding between messages
    }}
  >
    <Card
      sx={{
        bgcolor: message.sender === "user" ? '#90d3ff' : '#ededed',
        borderRadius: 2,
        maxWidth: { xs: '90%', sm: '70%', md: '60%' },
        wordBreak: 'break-word',
        overflowWrap: 'anywhere',
        boxShadow: 'none',
      }}
    >
      <CardContent
        sx={{
          padding: '12px',
        }}
      >
        {typeof message.text === 'string' ? (
          <ReactMarkdown
            children={message.text}
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
            components={{
              h1: ({ node, ...props }) => <Typography variant="h5" {...props} />,
              h2: ({ node, ...props }) => <Typography variant="h6" {...props} />,
              p: ({ node, ...props }) => <Typography variant="body1" {...props} />,
              li: ({ node, ...props }) => (
                <li>
                  <Typography variant="body1" {...props} />
                </li>
              ),
              code({ node, inline, className, children, ...props }) {
                return inline ? (
                  <code
                    style={{
                      backgroundColor: '#f5f5f5',
                      padding: '2px 4px',
                      borderRadius: '4px',
                      fontFamily: 'monospace',
                    }}
                    {...props}
                  >
                    {children}
                  </code>
                ) : (
                  <Box
                    component="pre"
                    sx={{
                      backgroundColor: '#f5f5f5',
                      padding: '10px',
                      borderRadius: '4px',
                      // overflow: 'auto', // Enable scrolling for long code blocks
                      // maxHeight: '900px',
                    }}
                  >
                    <code className={className} {...props}>
                      {children}
                    </code>
                  </Box>
                );
              },
              a: ({ node, ...props }) => (
                <Typography
                  component="a"
                  sx={{ color: 'primary.main', textDecoration: 'underline' }}
                  {...props}
                />
              ),
            }}
          />
        ) : (
          message.text
        )}
      </CardContent>
    </Card>
  </ListItem>
);

export default ChatMessage;