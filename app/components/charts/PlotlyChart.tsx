'use client';

import dynamic from 'next/dynamic';
import type { Data, Layout, Config } from 'plotly.js';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface PlotlyChartProps {
  data: Data[];
  layout?: Partial<Layout>;
  config?: Partial<Config>;
  className?: string;
}

export default function PlotlyChart({ data, layout, config, className }: PlotlyChartProps) {
  return (
    <Plot
      data={data}
      layout={{ autosize: true, template: 'plotly_white' as unknown as Layout['template'], ...layout }}
      config={{ displayModeBar: false, responsive: true, ...config }}
      className={className}
      style={{ width: '100%' }}
      useResizeHandler
    />
  );
}
