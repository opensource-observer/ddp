import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';
export default function DefiBuilderJourneys() {
  return <MarimoIframe notebookName="notebooks/insights/defi-builder-journeys" />;
}

export const metadata: Metadata = { title: 'DeFi Builder Journeys' };
