// import Header from '../components/Header';
import Navbar from '../components/Navbar';
import CircularProgress from '@mui/material/CircularProgress';
import CustomAlert from '../components/CustomAlert.tsx';
import React, { useState } from 'react';
import Footer from '../components/Footer.js';

const BGPLLaMa = () => {
    const [query, setQuery] = useState('');
    const [output, setOutput] = useState('');
    // const [existingQueries, setExistingQueries] = useState([]);
    const [error, setError] = useState(null);
    const [isLoaing, setIsLoading] = useState(false);
    const [alertOpen, setAlertOpen] = useState(false);

    // const handleQueryChange = (event) => {
    //     setQuery(event.target.value);
    // };

    const handleSubmit = (event) => {
        event.preventDefault(); // what does this do?
        if (!query.trim()) {
            setError('No input provided!')
            setAlertOpen(true);
            return;
        }

        setIsLoading(true);
        fetch('http://127.0.0.1:8000/api/bgp-llama?query=' + encodeURIComponent(query))
            .then(response => {
                if (!response.ok) {
                    setError('Network response error')
                    setAlertOpen(true);
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Intruction:', data.instruction);
                console.log('Output:', data.output);
                setOutput(data.output);
                // setExistingQueries(data.latest_insturctions);
            })
            .catch(error => {
                // prompt user of an error
                console.error('There was a problem with your fetch operation:', error);
                setError('There was a problem with your fetch operation: ' + error.message);
                setAlertOpen(true);
            })
            .finally(() => {
                setIsLoading(false);
            });
    };


    return (
        <div className="flex flex-col h-screen justify-between">
            {/* <Header /> */}
            <Navbar />
            <CustomAlert
                open={alertOpen}
                onClose={() => setAlertOpen(false)}
                severity="error"
                message={error}
            />
            <main className="mb-auto p-4"> {/* Main content grows to fill space */}
                <div className="container mx-auto">
                    <div className="flex justify-between">
                        <div className="w-2/3 ml-4">
                            <h2 className="font-bold mb-2">Welcome to BGP-LLaMA</h2>
                            <p className="mb-4">Enter your query in the text box below.</p>
                            <form onSubmit={handleSubmit}>
                                <div className="mb-4">
                                    <label htmlFor="queryInput" className="block mb-2">Input</label>
                                    <textarea
                                        id="queryInput"
                                        rows="4"
                                        className="w-full border p-2"
                                        placeholder="Enter your query here"
                                        value={query}
                                        onChange={(e) => setQuery(e.target.value)}
                                    />
                                </div>
                                {isLoaing ? (
                                    <div className="flex justify-center mt-4">
                                        <CircularProgress />
                                    </div>
                                ) : (
                                    <button
                                        type="submit"
                                        className="bg-gray-700 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded"
                                    >
                                        Submit
                                    </button>
                                )}
                            </form>
                            {!isLoaing && output && (
                                <div className="mt-4">
                                    <h3 className="font-bold mb-2">Model Output:</h3>
                                    <div className="border p-2 overflow-x-auto">
                                        <pre className="whitespace-pre-wrap"><code>{output}</code></pre>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
            <Footer />
        </div>
    );
};

export default BGPLLaMa;
