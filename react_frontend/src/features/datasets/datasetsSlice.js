import { createSlice } from '@reduxjs/toolkit';

const initialState = {
    allDatasets: [
            {
                title: 'Self-Instruct Generated Dataset',
                id: 'self-instruct-generated-dataset',
                datasets: [
                    {
                        id: 'bgp-knowledge',
                        title:'BGP Knowledge',
                        fileUrl: 'finetuning-dataset/self-instruct-generated-dataset/bgp-knowledge.json',
                        fileCount: 1111,
                        size: '10 MB',
                        fileType: 'json',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
                    },
                    {   
                        id: 'pybgpstream-base',
                        title:'PyBGPStream Base',
                        fileUrl: '/finetuning-dataset/self-instruct-generated-dataset/pybgpstream-base.json',
                        fileCount: 8609,
                        size: '10 MB',
                        fileType: 'json',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
                    },
                    {   
                        id: 'pybgpstream-real-time',
                        title:'PyBGPStream Real-time Stream',
                        fileUrl: '/finetuning-dataset/self-instruct-generated-dataset/pybgpstream-real-time.json',
                        fileCount: 1501,
                        size: '10 MB',
                        fileType: 'json',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
    
                    },
                ],
            },
            {
                title: 'Manual Seed Tasks',
                id: 'manual-seed-dataset',
                datasets: [
                    {
                        id: 'bgp-knowledge-1',
                        title:'BGP Knowledge I',
                        fileUrl: '/finetuning-dataset/manual-seed-dataset/bgp-knowledge-1.jsonl',
                        promptUrl: '/finetuning-dataset/manual-seed-dataset/prompt_knowledge.txt',
                        fileCount: 1111,
                        size: '10 MB',
                        fileType: 'jsonl',
                        promptType: 'txt',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
    
    
                    },
                    {
                        id: 'bgp-knowledge-2',
                        title:'BGP Knowledge II',
                        fileUrl: '/finetuning-dataset/manual-seed-dataset/bgp-knowledge-2.jsonl',
                        promptUrl: '/finetuning-dataset/manual-seed-dataset/prompt_knowledge.txt',
                        fileCount: 1111,
                        size: '10 MB',
                        fileType: 'jsonl',
                        promptType: 'txt',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
    
    
                    },
                    {
                        id: 'bgp-pybgpstream-base',
                        title:'PyBGPStream Base',
                        fileUrl: '/finetuning-dataset/manual-seed-dataset/bgp-pybgpstream-base.jsonl',
                        promptUrl: '/finetuning-dataset/manual-seed-dataset/prompt_pybgpstream.txt',
                        fileCount: 1111,
                        size: '10 MB',
                        fileType: 'jsonl',
                        promptType: 'txt',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
    
    
                    },
                    {
                        id: 'bgp-pybgpstream-real-case',
                        title:'PyBGPStream Real Cases',
                        fileUrl: '',
                        promptUrl: '/finetuning-dataset/manual-seed-dataset/prompt_pybgpstream.txt',
                        fileCount: 1111,
                        size: '10 MB',
                        fileType: 'jsonl',
                        promptType: 'txt',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
    
                    },
                    {
                        id: 'bgp-pybgpstream-real-time',
                        title:'PyBGPStream Real-time Stream',
                        fileUrl: '/finetuning-dataset/manual-seed-dataset/bgp-pybgpstream-real-time.jsonl',
                        promptUrl: '/finetuning-dataset/manual-seed-dataset/prompt-pybgpstream-realtime.txt',
                        fileCount: 1111,
                        size: '10 MB',
                        fileType: 'jsonl',
                        promptType: 'txt',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
                    },             
                ]
            },
            // other sections
    ],
    loading: false,
    error: null
};

const datasetsSlice = createSlice({
    name: 'datasets',
    initialState,
    reducers: {
        addDatasetToSection: (state, action) => {
            const { sectionTitle, newDataset } = action.payload;
            const section = state.allDatasets.find(section => section.title === sectionTitle);
            if (section) {
                section.datasets.push(newDataset);
            }
        },        
        removeDatasetFromSection: (state, action) => {
            const { sectionTitle, datasetId } = action.payload;
            const section = state.allDatasets.find(section => section.title === sectionTitle);
            if (section) {
                section.datasets = section.datasets.filter(dataset => dataset.id !== datasetId);
            }
        },        
        updateDatasetInSection: (state, action) => {
            const { sectionTitle, updatedDataset } = action.payload;
            const section = state.allDatasets.find(section => section.title === sectionTitle);
            if (section) {
                const index = section.datasets.findIndex(dataset => dataset.id === updatedDataset.id);
                if (index !== -1) {
                    section.datasets[index] = updatedDataset;
                }
            }
        },        
        // Additional reducers for adding, removing, or updating whole sections could be added here
    }
});

export const { addDatasetToSection, removeDatasetFromSection, updateDatasetInSection } = datasetsSlice.actions;
export default datasetsSlice.reducer;

// Initial State: Defined starting state for the slice.
// Reducers: Functions defining how state changes in response to actions. These update the state based on the type of action and the payload provided.
// Action Creators: Automatically generated functions (addDataset, removeDataset, updateDataset) that you can call to create action objects to dispatch to the store.