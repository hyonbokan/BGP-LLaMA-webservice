import { configureStore } from '@reduxjs/toolkit';
import datasetsReducer from '../features/dataset/datasetsSlice';

export const store = configureStore({
    reducer: {
        datasets: datasetsReducer,
    },
});