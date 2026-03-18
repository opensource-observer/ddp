import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';
export default function DeveloperRetention() {
  return <MarimoIframe notebookName="notebooks/insights/developer-retention" />;
}

export const metadata: Metadata = { title: 'Retention Analysis' };
