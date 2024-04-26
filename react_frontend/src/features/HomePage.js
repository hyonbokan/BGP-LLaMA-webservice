import Header from '../components/Header';
import Navbar from '../components/Navbar';


const HomePage = () => {
    return (
        <div>
            <Header />
            <Navbar />
            <div className="text-center p-4">
                <p className="mt-2">
                Welcome to BGP-LLaMA webservice
                </p>
                <p className="text-sm mt-2">
                BGP-LLaMA is a BGP routing-specialized fine-tuned LLM, capable of interpreting and responding to BGP queries or instructions as well as generating BGP routing data analysis codes for various BGP analysis or anomaly detection tasks
                </p>
            </div>
        </div>
    );
};

export default HomePage;