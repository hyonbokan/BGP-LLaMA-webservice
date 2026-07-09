import { useParams } from 'react-router-dom';
import { findDataset } from '@/data/datasets';
import { apiUrl } from '@/config';

export function useDatasetDetails() {
  const { sectionId, datasetId } = useParams();
  const dataset = findDataset(sectionId, datasetId) ?? null;

  const handleDownload = async (fileUrl: string, fileName: string, fileExtension = '') => {
    const relativeFileUrl = fileUrl.replace(/^\/+/, '');
    const url = apiUrl(`download?file=${encodeURIComponent(relativeFileUrl)}`);
    try {
      const response = await fetch(url, { method: 'GET', credentials: 'include' });
      if (!response.ok) throw new Error(`Download failed (${response.status})`);
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `${fileName}${fileExtension ? '.' + fileExtension : ''}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Error downloading the file:', error);
      throw error;
    }
  };

  return { dataset, sectionId, handleDownload };
}
