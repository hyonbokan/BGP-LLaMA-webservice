import { configureStore } from '@reduxjs/toolkit';
import datasetsReducer from './features/datasets/datasetsSlice';

export const store = configureStore({
    reducer: {
        datasets: datasetsReducer,
    },
});