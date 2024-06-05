import {
  BrowserRouter as Router,
  Route,
  Routes
} from 'react-router-dom';
import HomePage from './features/HomePage';
import DatasetPage from './features/DatasetPage';
import BGPLLaMA from './features/BGPLLaMA';
import DetailPage from './features/DetailPage';
import NotFoundPage from './features/NotFoundPage';
import BGPchat from './features/BGPchat';

function App() {
  return (
    <Router>
      <div className="App m-0">
        <main>
          <Routes>
            <Route path='/' element={<HomePage />} />
            <Route path='/dataset' element={<DatasetPage />} />
            {/* <Route path='/bgp_llama' element={<BGPLLaMA />} /> */}
            <Route path='/dataset/:sectionId/:datasetId' element={<DetailPage />} />
            <Route path='/bgp_chat' element={<BGPchat />} />
            {/* Catch-All Route */}
            <Route path='*' element={<NotFoundPage />} />
          </Routes>
        </main>
    </div>
    </Router>
  );
}

export default App;
