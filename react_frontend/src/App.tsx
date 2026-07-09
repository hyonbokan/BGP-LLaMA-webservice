import { useEffect } from 'react';
import { Route, Routes } from 'react-router-dom';
import { fetchCsrfToken } from '@/lib/api';
import { RootLayout, ChatLayout } from '@/components/layout/layouts';
import { HomePage } from '@/pages/home-page';
import { DatasetPage } from '@/pages/dataset-page';
import { DetailPage } from '@/pages/detail-page';
import { FineTuningPage } from '@/pages/fine-tuning-page';
import { BgpChatPage } from '@/pages/bgp-chat-page';
import { NotFoundPage } from '@/pages/not-found-page';

export function App() {
  // Prime the CSRF cookie once so later mutating requests are accepted.
  useEffect(() => {
    void fetchCsrfToken();
  }, []);

  return (
    <Routes>
      <Route element={<RootLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/dataset" element={<DatasetPage />} />
        <Route path="/dataset/:sectionId/:datasetId" element={<DetailPage />} />
        <Route path="/finetuning" element={<FineTuningPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
      {/* Chat is a full-height workspace — its own chrome, no footer. */}
      <Route element={<ChatLayout />}>
        <Route path="/bgp_chat" element={<BgpChatPage />} />
      </Route>
    </Routes>
  );
}
