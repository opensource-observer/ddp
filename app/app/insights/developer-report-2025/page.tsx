import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';
export default function DeveloperReport2025() {
  return <MarimoIframe notebookName="notebooks/insights/developer-report-2025" />;
}

export const metadata: Metadata = { title: '2025 Developer Trends' };
