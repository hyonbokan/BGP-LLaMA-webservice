import { Route, Routes } from 'react-router-dom';
import { ContentLayout, WorkspaceLayout } from '@/components/layout/layouts';
import { HomePage } from '@/pages/home-page';
import { DatasetPage } from '@/pages/dataset-page';
import { DetailPage } from '@/pages/detail-page';
import { BgpChatPage } from '@/pages/bgp-chat-page';
import { BgpAgentPage } from '@/pages/bgp-agent-page';
import { NotFoundPage } from '@/pages/not-found-page';

export function App() {
  return (
    <Routes>
      <Route element={<ContentLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/dataset" element={<DatasetPage />} />
        <Route path="/dataset/:sectionId/:datasetId" element={<DetailPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
      {/* Full-height feature workspaces — their own chrome, no footer. */}
      <Route element={<WorkspaceLayout />}>
        <Route path="/bgp_chat" element={<BgpChatPage />} />
        <Route path="/bgp_agent" element={<BgpAgentPage />} />
      </Route>
    </Routes>
  );
}
