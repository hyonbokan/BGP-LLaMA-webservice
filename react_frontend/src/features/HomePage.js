import Navbar from '../components/PageComponents/Navbar';
import Footer from '../components/PageComponents/Footer';
import HomePageTutorial from '../components/HomePageTutorial';
import { Container, Typography, Button, Grid, Card, CardContent, Box } from '@mui/material';
import { Link } from 'react-router-dom';

const HomePage = () => {
  const cards = [
    {
      title: "BGP-LLaMA documentation",
      description: "Learn how to interact with BGP-LLaMA.",
      gradient: "linear-gradient(145deg, rgba(255,255,255,1) 0%, rgba(214,214,255,1) 100%)"
    },
    {
      title: "Create Your Custom Dataset",
      description: "Use 'Self-Instruct' framework to generate your custom dataset.",
      gradient: "linear-gradient(145deg, rgba(235,235,255,1) 0%, rgba(215,215,255,1) 100%)"
    },
    {
      title: "GitHub Repository",
      description: "Our GitHub repository with instruction-funetuning tutorial.",
      gradient: "linear-gradient(145deg, rgba(245,245,255,1) 0%, rgba(225,225,255,1) 100%)"
    }
  ];
  
    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <Navbar />
            <Container component="main" sx={{ flexGrow: 1, width: 'auto', padding: '24px' }}>
                {/* Hero Section */}
                <Container sx={{ py: 8, textAlign: 'center' }}>
                    <Typography variant="h3" gutterBottom>
                    Welcome to BGP-LLaMA
                    </Typography>
                    <Typography variant="h6" color="textSecondary" paragraph>
                    BGP-LLaMA is an instruction-finetuned, open-source LLM on BGP routing knowledge and analysis
                    </Typography>
                    <Button variant="contained" color="primary">
                      <Link to="/bgp_chat">
                        Get Started
                      </Link>
                    </Button>
                </Container>

                {/* Middle section */}
                <HomePageTutorial />

                {/* Bottom section */}
                <Box sx={{ flexGrow: 1, padding: '5px' }}>
                  {/* bottom cards */}
                  <Grid container spacing={2}>
                    {cards.map((card, index) => (
                      <Grid item xs={12} sm={6} md={4} key={index}>
                        <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', background: card.gradient }}>
                          <CardContent sx={{ flexGrow: 1 }}>
                            <Typography gutterBottom variant="h5" component="h2">
                              {card.title}
                            </Typography>
                            <Typography>
                              {card.description}
                            </Typography>
                          </CardContent>
                          <Box sx={{ p: 2, textAlign: 'center' }}>
                            <Button size="small">Learn More</Button>
                          </Box>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                  {/* bottom cards */}
                </Box>
            </Container>
            <Footer />
        </Box>
      );
    };

export default HomePage;