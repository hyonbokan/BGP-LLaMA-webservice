import React, { useState } from 'react';
import { Box, Button, TextField, Typography, MenuItem, FormControl, InputLabel, Select, Checkbox, FormControlLabel, FormGroup, Grid, CircularProgress, Paper } from '@mui/material';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const FineTuningPage = () => {
    const [model, setModel] = useState('');
    const [customModel, setCustomModel] = useState('');
    const [finetunedModelName, setFinetunedModelName] = useState('');
    const [datasets, setDatasets] = useState({
        'bgp-pybgpstream-base': false,
        'bgp-pybgpstream-real-case': false,
        'bgp-pybgpstream-real-time': false,
        'bgp-knowledge-1': false,
        'bgp-knowledge-2': false,
    });
    const [testSamples, setTestSamples] = useState('');
    const [userDataset, setUserDataset] = useState(null);
    const [hyperparameters, setHyperparameters] = useState({
        lora_alpha: 16,
        lora_dropout: 0.1,
        lora_r: 64,
        per_device_train_batch_size: 4,
        gradient_accumulation_steps: 1,
        optim: 'paged_adamw_32bit',
        save_steps: 200,
        logging_steps: 500,
        learning_rate: 1e-4,
        max_grad_norm: 0.3,
        max_steps: 10000,
        warmup_ratio: 0.05,
        lr_scheduler_type: 'cosine',
    });
    const [isLoading, setIsLoading] = useState(false);

    const handleModelChange = (event) => {
        setModel(event.target.value);
    };

    const handleDatasetChange = (event) => {
        setDatasets({
            ...datasets,
            [event.target.name]: event.target.checked,
        });
    };

    const handleHyperparameterChange = (event) => {
        setHyperparameters({
            ...hyperparameters,
            [event.target.name]: event.target.value,
        });
    };

    const handleUserDatasetChange = (event) => {
        setUserDataset(event.target.files[0]);
    };

    const handleStartFineTuning = () => {
        setIsLoading(true);
        // Dispatch an action or call an API to start fine-tuning
        setTimeout(() => {
            setIsLoading(false);
            alert('Fine-tuning started!');
        }, 2000); // Simulate an API call
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <Navbar />
            <Box component='main' sx={{ flexGrow: 1, padding: '24px' }}>
                <Typography variant='h4' sx={{ fontFamily: 'monospace', fontWeight: 600, mb: 4 }}>
                    Fine-Tune LLM Model
                </Typography>
                <Grid container spacing={4}>
                    <Grid item xs={12} md={6}>
                        <Paper sx={{ padding: 3 }}>
                            <Typography variant='h6' sx={{ fontFamily: 'monospace', fontWeight: 600, mb: 2 }}>
                                Model Selection
                            </Typography>
                            <FormControl fullWidth sx={{ mb: 3 }}>
                                <InputLabel id="model-label">LLM Model</InputLabel>
                                <Select
                                    labelId="model-label"
                                    id="model"
                                    value={model}
                                    onChange={handleModelChange}
                                    label="LLM Model"
                                >
                                    <MenuItem value="LLaMA 7B">LLaMA 7B</MenuItem>
                                    <MenuItem value="LLaMA 13B">LLaMA 13B</MenuItem>
                                    <MenuItem value="LLaMA 70B">LLaMA 70B</MenuItem>
                                    <MenuItem value="Other">Other</MenuItem>
                                </Select>
                            </FormControl>
                            {model === 'Other' && (
                                <TextField
                                    fullWidth
                                    label="Custom Model"
                                    value={customModel}
                                    onChange={(e) => setCustomModel(e.target.value)}
                                    sx={{ mb: 3 }}
                                />
                            )}
                            <TextField
                                fullWidth
                                label="Name of the Fine-tuned Model"
                                value={finetunedModelName}
                                onChange={(e) => setFinetunedModelName(e.target.value)}
                                sx={{ mb: 3 }}
                            />
                        </Paper>
                    </Grid>

                    <Grid item xs={12} md={6}>
                        <Paper sx={{ padding: 3 }}>
                            <Typography variant='h6' sx={{ fontFamily: 'monospace', fontWeight: 600, mb: 2 }}>
                                Dataset Selection
                            </Typography>
                            <Grid container spacing={2}>
                                <Grid item xs={12} sm={6}>
                                    <Typography variant='subtitle1' sx={{ fontFamily: 'monospace', fontWeight: 600, mb: 1 }}>
                                        BGP PyBGPStream Datasets
                                    </Typography>
                                    <FormGroup>
                                        {['bgp-pybgpstream-base', 'bgp-pybgpstream-real-case', 'bgp-pybgpstream-real-time'].map((key) => (
                                            <FormControlLabel
                                                control={
                                                    <Checkbox
                                                        checked={datasets[key]}
                                                        onChange={handleDatasetChange}
                                                        name={key}
                                                    />
                                                }
                                                label={key.replace(/-/g, ' ')}
                                                key={key}
                                            />
                                        ))}
                                    </FormGroup>
                                </Grid>
                                <Grid item xs={12} sm={6}>
                                    <Typography variant='subtitle1' sx={{ fontFamily: 'monospace', fontWeight: 600, mb: 1 }}>
                                        BGP Knowledge Datasets
                                    </Typography>
                                    <FormGroup>
                                        {['bgp-knowledge-1', 'bgp-knowledge-2'].map((key) => (
                                            <FormControlLabel
                                                control={
                                                    <Checkbox
                                                        checked={datasets[key]}
                                                        onChange={handleDatasetChange}
                                                        name={key}
                                                    />
                                                }
                                                label={key.replace(/-/g, ' ')}
                                                key={key}
                                            />
                                        ))}
                                    </FormGroup>
                                </Grid>
                                <Grid item xs={12}>
                                    <Typography variant='subtitle1' sx={{ fontFamily: 'monospace', fontWeight: 600, mb: 1 }}>
                                        User Dataset
                                    </Typography>
                                    <Button variant="contained" component="label">
                                        Upload File
                                        <input type="file" hidden onChange={handleUserDatasetChange} />
                                    </Button>
                                    {userDataset && (
                                        <Typography variant='body2' sx={{ fontFamily: 'monospace', mt: 2 }}>
                                            {userDataset.name}
                                        </Typography>
                                    )}
                                    <Typography variant='body2' sx={{ fontFamily: 'monospace', mt: 2 }}>
                                        Note: Please upload a dataset in the following format: [placeholder for dataset format description].
                                    </Typography>
                                </Grid>
                            </Grid>
                        </Paper>
                    </Grid>

                    <Grid item xs={12}>
                        <Paper sx={{ padding: 3 }}>
                            <Typography variant='h6' sx={{ fontFamily: 'monospace', fontWeight: 600, mb: 2 }}>
                                Train/Test Split
                            </Typography>
                            <TextField
                                fullWidth
                                label="Number of Test Samples"
                                value={testSamples}
                                onChange={(e) => setTestSamples(e.target.value)}
                                sx={{ mb: 3 }}
                            />
                        </Paper>
                    </Grid>

                    <Grid item xs={12}>
                        <Paper sx={{ padding: 3 }}>
                            <Typography variant='h6' sx={{ fontFamily: 'monospace', fontWeight: 600, mb: 2 }}>
                                Hyperparameters
                            </Typography>
                            <Grid container spacing={2}>
                                <Grid item xs={12} sm={4}>
                                    <TextField
                                        fullWidth
                                        label="Lora Alpha"
                                        type="number"
                                        name="lora_alpha"
                                        value={hyperparameters.lora_alpha}
                                        onChange={handleHyperparameterChange}
                                        sx={{ mb: 3 }}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={4}>
                                    <TextField
                                        fullWidth
                                        label="Lora Dropout"
                                        type="number"
                                        name="lora_dropout"
                                        value={hyperparameters.lora_dropout}
                                        onChange={handleHyperparameterChange}
                                        sx={{ mb: 3 }}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={4}>
                                    <TextField
                                        fullWidth
                                        label="Lora R"
                                        type="number"
                                        name="lora_r"
                                        value={hyperparameters.lora_r}
                                        onChange={handleHyperparameterChange}
                                        sx={{ mb: 3 }}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={4}>
                                    <TextField
                                        fullWidth
                                        label="Per Device Train Batch Size"
                                        type="number"
                                        name="per_device_train_batch_size"
                                        value={hyperparameters.per_device_train_batch_size}
                                        onChange={handleHyperparameterChange}
                                        sx={{ mb: 3 }}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={4}>
                                    <TextField
                                        fullWidth
                                        label="Gradient Accumulation Steps"
                                        type="number"
                                        name="gradient_accumulation_steps"
                                        value={hyperparameters.gradient_accumulation_steps}
                                        onChange={handleHyperparameterChange}
                                        sx={{ mb: 3 }}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={4}>
                                    <TextField
                                        fullWidth
                                        label="Optimizer"
                                        name="optim"
                                        value={hyperparameters.optim}
                                        onChange={handleHyperparameterChange}
                                        sx={{ mb: 3 }}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={4}>
                                    <TextField
                                        fullWidth
                                        label="Save Steps"
                                        type="number"
                                        name="save_steps"
                                        value={hyperparameters.save_steps}
                                        onChange={handleHyperparameterChange}
                                        sx={{ mb: 3 }}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={4}>
                                    <TextField
                                        fullWidth
                                        label="Logging Steps"
                                        type="number"
                                        name="logging_steps"
                                        value={hyperparameters.logging_steps}
                                        onChange={handleHyperparameterChange}
                                        sx={{ mb: 3 }}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={4}>
                                    <TextField
                                        fullWidth
                                        label="Learning Rate"
                                        type="number"
                                        name="learning_rate"
                                        value={hyperparameters.learning_rate}
                                        onChange={handleHyperparameterChange}
                                        sx={{ mb: 3 }}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={4}>
                                    <TextField
                                        fullWidth
                                        label="Max Grad Norm"
                                        type="number"
                                        name="max_grad_norm"
                                        value={hyperparameters.max_grad_norm}
                                        onChange={handleHyperparameterChange}
                                        sx={{ mb: 3 }}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={4}>
                                    <TextField
                                        fullWidth
                                        label="Max Steps"
                                        type="number"
                                        name="max_steps"
                                        value={hyperparameters.max_steps}
                                        onChange={handleHyperparameterChange}
                                        sx={{ mb: 3 }}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={4}>
                                    <TextField
                                        fullWidth
                                        label="Warmup Ratio"
                                        type="number"
                                        name="warmup_ratio"
                                        value={hyperparameters.warmup_ratio}
                                        onChange={handleHyperparameterChange}
                                        sx={{ mb: 3 }}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={4}>
                                    <TextField
                                        fullWidth
                                        label="LR Scheduler Type"
                                        name="lr_scheduler_type"
                                        value={hyperparameters.lr_scheduler_type}
                                        onChange={handleHyperparameterChange}
                                        sx={{ mb: 3 }}
                                    />
                                </Grid>
                            </Grid>
                        </Paper>
                    </Grid>
                </Grid>

                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                    <Button variant="contained" color="primary" onClick={handleStartFineTuning} disabled={isLoading}>
                        {isLoading ? <CircularProgress size={24} /> : 'Start Fine-Tuning'}
                    </Button>
                </Box>
            </Box>
            <Footer />
        </Box>
    );
};

export default FineTuningPage;