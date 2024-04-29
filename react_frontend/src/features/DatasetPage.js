import Header from '../components/Header';
import Navbar from '../components/Navbar';



const DatasetPage = () => {
    // URLs for downloading the files
    const fileUrls = {
        bgpKnowledge: '',
        pyBGPStreamBase: '',
        pyBGPStreamRealTime: '',
    }
    return (
        <div>
            <Header />
            <Navbar />
            <h1>Training Data</h1>
            <ul>
                <li><a href={fileUrls.bgpKnowledge} download>BGP Knowledge</a></li>
                <li><a href={fileUrls.pyBGPStreamBase} download>PyBGPStream Base</a></li>
                <li><a href={fileUrls.pyBGPStreamRealTime} download>PyBGPStream Real-time Stream</a></li>
            </ul>
            <h1>Manual Seed Tasks</h1>
        </div>
    );
};

export default DatasetPage;