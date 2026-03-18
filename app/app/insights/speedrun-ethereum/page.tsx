import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';
export default function SpeedrunEthereum() {
  return <MarimoIframe notebookName="notebooks/insights/speedrun-ethereum" />;
}

export const metadata: Metadata = { title: 'Speedrun Ethereum' };
