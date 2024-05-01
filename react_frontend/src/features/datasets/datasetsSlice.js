import { createSlice } from '@reduxjs/toolkit';

const initialState = {
    allDatasets: [
            {
                title: 'Self-Instruct Generated Dataset',
                datasets: [
                    {
                        id: 'self-instruct-bgp-knowledge',
                        title:'BGP Knowledge',
                        imageUrl: '',
                        fileCount: 1111,
                        size: '10 MB',
                        fileType: 'json',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
                    },
                    {   
                        id: 'self-instruct-pybgpstream-base',
                        title:'PyBGPStream Base',
                        imageUrl: '',
                        fileCount: 1111,
                        size: '10 MB',
                        fileType: 'json',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
                    },
                    {   
                        id: 'self-instruct-pybgpstream-real-time',
                        title:'PyBGPStream Real-time Stream',
                        imageUrl: '',
                        fileCount: 1111,
                        size: '10 MB',
                        fileType: 'json',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
    
                    },
                ],
            },
            // other dataset
            {
                title: 'Manual Seed Tasks',
                datasets: [
                    {
                        id: 'manual-seed-bgp-knowledge-1',
                        title:'BGP Knowledge I',
                        imageUrl: '',
                        fileCount: 1111,
                        size: '10 MB',
                        fileType: 'json',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
    
    
                    },
                    {
                        id: 'manual-seed-bgp-knowledge-2',
                        title:'BGP Knowledge II',
                        imageUrl: '',
                        fileCount: 1111,
                        size: '10 MB',
                        fileType: 'json',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
    
    
                    },
                    {
                        id: 'manual-seed-bgp-pybgpstream-base',
                        title:'PyBGPStream Base',
                        imageUrl: '',
                        fileCount: 1111,
                        size: '10 MB',
                        fileType: 'json',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
    
    
                    },
                    {
                        id: 'manual-seed-bgp-pybgpstream-real-case',
                        title:'PyBGPStream Real Cases',
                        imageUrl: '',
                        fileCount: 1111,
                        size: '10 MB',
                        fileType: 'json',
                        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
    
                    },
                    {
                        id: 'manual-seed-bgp-pybgpstream-real-time',
                        title:'PyBGPStream Real-time Stream',
                        imageUrl: '',
                        fileCount: 1111,
                        size: '10 MB',
                        fileType: 'json',
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
            const { sectionTitle, dataset } = action.payload;
            const section = state.allDatasets.find(sec => sec.title === sectionTitle);
            if (section) {
                section.datasets.push(dataset);
            }
        },
        removeDatasetFromSection: (state, action) => {
            const { sectionTitle, datasetId } = action.payload;
            const section = state.allDatasets.find(sec => sec.title === sectionTitle);
            if (section) {
                section.datasets = section.datasets.filter(ds => ds.id !== datasetId);
            }
        },
        updateDatasetInSection: (state, action) => {
            const { sectionTitle, dataset } = action.payload;
            const section = state.allDatasets.find(sec => sec.title === sectionTitle);
            if (section) {
                const index = section.datasets.findIndex(ds => ds.id === dataset.id);
                if (index !== -1) {
                    section.datasets[index] = dataset;
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