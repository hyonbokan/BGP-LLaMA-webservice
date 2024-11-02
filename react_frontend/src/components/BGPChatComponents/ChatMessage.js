import React from 'react';
import { ListItem, Card, CardContent, Typography } from '@mui/material';
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
    }}
  >
    <Card
      sx={{
        bgcolor: message.sender === "user" ? '#90d3ff' : '#ededed',
        borderRadius: 2,
        maxWidth: '70%',
      }}
    >
      <CardContent>
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
                    }}
                    {...props}
                  >
                    {children}
                  </code>
                ) : (
                  <pre
                    style={{
                      backgroundColor: '#f5f5f5',
                      padding: '10px',
                      borderRadius: '4px',
                      overflow: 'auto',
                    }}
                  >
                    <code className={className} {...props}>
                      {children}
                    </code>
                  </pre>
                );
              },
            }}
          />
        ) : (
          // If message.text is a React element, render it directly
          message.text
        )}
      </CardContent>
    </Card>
  </ListItem>
);

export default ChatMessage;

// const ChatMessage = ({ message }) => (
//     <ListItem
//         alignItems="flex-start"
//         sx={{
//             display: 'flex',
//             flexDirection: message.sender === "user" ? 'row-reverse' : 'row',
//         }}
//     >
//         <Card
//             sx={{
//                 bgcolor: message.sender === "user" ? '#90d3ff' : '#ededed',
//                 borderRadius: 2,
//                 maxWidth: '70%',
//             }}
//         >
//             <CardContent>
//                 <Typography
//                     sx={{
//                         fontFamily: 'monospace',
//                         fontWeight: 'medium',
//                         color: 'black',
//                         textAlign: 'justify',
//                         whiteSpace: 'pre-line',
//                     }}
//                 >
//                     {message.text}
//                 </Typography>
//             </CardContent>
//         </Card>
//     </ListItem>
// );

// export default ChatMessage;