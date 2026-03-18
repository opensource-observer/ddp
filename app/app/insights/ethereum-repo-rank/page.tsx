import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';
export default function EthereumRepoRank() {
  return <MarimoIframe notebookName="notebooks/insights/ethereum-repo-rank" />;
}

export const metadata: Metadata = { title: 'Ethereum Repo Rank' };
