import { useParams } from 'react-router-dom';
import { useSelector } from 'react-redux';

const useDatasetDetails = () => {
    const { sectionId, datasetId } = useParams();

    // Fetch dataset details from Redux store
    const dataset = useSelector(state => {
        const section = state.datasets.allDatasets.find(sec => sec.id === sectionId);
        return section ? section.datasets.find(ds => ds.id === datasetId) : null;
    });

    // File download handler
    const handleDownload = (fileUrl, fileName, fileExtension = '') => {
        const relativeFileUrl = fileUrl.replace(/^\/+/, '');
        const url = `https://llama.cnu.ac.kr/api/download?file=${encodeURIComponent(relativeFileUrl)}`;

        fetch(url, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
            }
        })
        .then(response => response.blob())
        .then(blob => {
            const downloadUrl = window.URL.createObjectURL(new Blob([blob]));
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.setAttribute('download', `${fileName}${fileExtension ? '.' + fileExtension : ''}`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
        })
        .catch(error => console.error('Error downloading the file: ', error));
    };

    return { dataset, sectionId, handleDownload };
};

export default useDatasetDetails;
