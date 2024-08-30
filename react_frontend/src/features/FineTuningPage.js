import React, { useState } from 'react';
import { Box, Button, TextField, Typography, MenuItem, FormControl, InputLabel, Select, Checkbox, FormControlLabel, FormGroup, Grid, CircularProgress, Paper } from '@mui/material';
import Navbar from '../components/PageComponents/Navbar';
import Footer from '../components/PageComponents/Footer';
import CustomAlert from '../components/CustomAlert.tsx';
import axiosInstance from '../utils/axiosInstance';
import { useSelector } from 'react-redux';

const FineTuningPage = () => {
    const allDatasets = useSelector(state => state.datasets.allDatasets);
    const [model, setModel] = useState('');
    const [customModel, setCustomModel] = useState('');
    const [finetunedModelName, setFinetunedModelName] = useState('');
    const [selectedDatasets, setSelectedDatasets] = useState([]);
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
    const [fineTuningStatus, setFineTuningStatus] = useState('');
    const [alert, setAlert] = useState({ open: false, massage: 'Oops, an error occurred!', severity: 'error' });

    const handleModelChange = (event) => {
        setModel(event.target.value);
    };

    const handleDatasetChange = (event) => {
        const { name, checked } = event.target;
        const dataset = allDatasets.flatMap(group => group.datasets).find(d => d.id === name);
        if (checked) {
            setSelectedDatasets([...selectedDatasets, dataset.fileUrl]);
        } else {
            setSelectedDatasets(selectedDatasets.filter(url => url !== dataset.fileUrl));
        }
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

    const validateForm = () => {
        const errors = [];

        if (!model) errors.push('Please select a model.');
        if (!finetunedModelName) errors.push('Please enter a name for the finetuned model.');
        if (selectedDatasets.length === 0 && !userDataset) errors.push('Please select at least one dataset or upload a your own custom dataset.');
        for (const key in hyperparameters) {
            if (!hyperparameters[key]) errors.push(`Please fill in the ${key.replace(/_/g, '')} field.`);
        }

        if (errors.length > 0) {
            return errors.join(' ');
        }
        return null;
    };

    const handleStartFineTuning = () => {
        const validationError = validateForm();
        if (validationError) {
            // console.log(validationError)
            setAlert({ open: true, message: validationError, severity: 'error' });
            return;
        }

        setIsLoading(true);

        const formData = new FormData();
        formData.append('model_id', model === 'Other' ? customModel : model);
        formData.append('finetuned_model_name', finetunedModelName);
        formData.append('datasets', JSON.stringify(selectedDatasets));
        formData.append('test_samples', testSamples);
        formData.append('hyperparameters', JSON.stringify(hyperparameters));
        if (userDataset) {
            formData.append('user_dataset', userDataset);
        }

        console.log('Form Data Sent to Backend:', {
            model_id: model === 'Other' ? customModel : model,
            datasets: selectedDatasets,
            test_samples: testSamples,
            hyperparameters,
            user_dataset: userDataset ? userDataset.name : null
        });

        axiosInstance.post('finetuning', formData)
            .then(response => {
                console.log('Fine-tuning started:', response.data);
                setFineTuningStatus('Fine-tuning started successfully.');
                setIsLoading(false);
            })
            .catch(error => {
                console.error('Error starting fine-tuning:', error);
                setFineTuningStatus('Error starting fine-tuning.');
                setIsLoading(false);
            });
    };

    const hyperparameterFields = [
        { label: 'Lora Alpha', name: 'lora_alpha', type: 'number' },
        { label: 'Lora Dropout', name: 'lora_dropout', type: 'number' },
        { label: 'Lora R', name: 'lora_r', type: 'number' },
        { label: 'Per Device Train Batch Size', name: 'per_device_train_batch_size', type: 'number' },
        { label: 'Gradient Accumulation Steps', name: 'gradient_accumulation_steps', type: 'number' },
        { label: 'Optimizer', name: 'optim', type: 'text' },
        { label: 'Save Steps', name: 'save_steps', type: 'number' },
        { label: 'Logging Steps', name: 'logging_steps', type: 'number' },
        { label: 'Learning Rate', name: 'learning_rate', type: 'number' },
        { label: 'Max Grad Norm', name: 'max_grad_norm', type: 'number' },
        { label: 'Max Steps', name: 'max_steps', type: 'number' },
        { label: 'Warmup Ratio', name: 'warmup_ratio', type: 'number' },
        { label: 'LR Scheduler Type', name: 'lr_scheduler_type', type: 'text' },
    ];

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <Navbar />
            <Box component='main' sx={{ flexGrow: 1, padding: '24px' }}>
                <Typography variant='h4' sx={{ fontFamily: 'monospace', fontWeight: 600, mb: 4 }}>
                    Fine-Tune LLM
                </Typography>
                <Grid container spacing={4}>
                    <Grid item xs={12} md={6}>
                        <Paper sx={{ padding: 3 }}>
                            <Typography variant='h6' sx={{ fontFamily: 'monospace', fontWeight: 600, mb: 2 }}>
                                LLM Selection
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
                                    <MenuItem value="meta-llama/Llama-2-7b-chat-hf">LLaMA 2 7B</MenuItem>
                                    <MenuItem value="meta-llama/Llama-2-13b-chat-hf">LLaMA 2 13B</MenuItem>
                                    <MenuItem value="meta-llama/Llama-2-70b-chat-hf">LLaMA 2 70B</MenuItem>
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
                                {allDatasets.filter(dataset => dataset.id === 'self-instruct-generated-dataset').map((dataset) => (
                                    <Grid item xs={12} key={dataset.id}>
                                        <Typography variant='subtitle1' sx={{ fontFamily: 'monospace', fontWeight: 600, mb: 1 }}>
                                        </Typography>
                                        <FormGroup>
                                            {dataset.datasets.map((subDataset) => (
                                                <FormControlLabel
                                                    control={
                                                        <Checkbox
                                                            checked={selectedDatasets.includes(subDataset.fileUrl)}
                                                            onChange={handleDatasetChange}
                                                            name={subDataset.id}
                                                        />
                                                    }
                                                    label={subDataset.title}
                                                    key={subDataset.id}
                                                />
                                            ))}
                                        </FormGroup>
                                    </Grid>
                                ))}
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
                                {hyperparameterFields.map((field) => (
                                    <Grid item xs={12} sm={4} key={field.name}>
                                        <TextField
                                            fullWidth
                                            label={field.label}
                                            type={field.type}
                                            name={field.name}
                                            value={hyperparameters[field.name]}
                                            onChange={handleHyperparameterChange}
                                            sx={{ mb: 3 }}
                                        />
                                    </Grid>
                                ))}
                            </Grid>
                        </Paper>
                    </Grid>
                </Grid>

                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                    <Button variant="contained" color="primary" onClick={handleStartFineTuning} disabled={isLoading}>
                        {isLoading ? <CircularProgress size={24} /> : 'Start Fine-Tuning'}
                    </Button>
                </Box>
                {fineTuningStatus && (
                    <Typography variant="body2" sx={{ mt: 2, textAlign: 'center', fontFamily: 'monospace' }}>
                        {fineTuningStatus}
                    </Typography>
                )}
            </Box>
            <CustomAlert
                severity={alert.severity}
                message={alert.message}
                open={alert.open}
                onClose={() => setAlert({ ...alert, open: false })}
            />
            <Footer />
        </Box>
    );
};

export default FineTuningPage;