import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';
export default function DeveloperLifecycle() {
  return <MarimoIframe notebookName="notebooks/insights/developer-lifecycle" />;
}

export const metadata: Metadata = { title: 'Lifecycle Analysis' };
