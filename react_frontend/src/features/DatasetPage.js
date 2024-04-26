import Header from '../components/Header';
import Navbar from '../components/Navbar';



const DatasetPage = () => {
    return (
        <div>
            <Header />
            <Navbar />
            <h1>Training Data</h1>
            <ul>
                <li>BGP Knowledge</li>
                <li>PyBGPStream Base</li>
                <li>PyBGPStream Real-time Stream</li>
            </ul>
        </div>
    );
};

export default DatasetPage;