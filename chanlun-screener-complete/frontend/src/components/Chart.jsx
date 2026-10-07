import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { Spin, message, Empty } from 'antd';
import { stockApi } from '../api';

export default function Chart({ ticker }) {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!ticker) return;
    loadChart();
  }, [ticker]);

  const loadChart = async () => {
    setLoading(true);
    try {
      const { data } = await stockApi.getChart(ticker);
      const parsed = JSON.parse(data.chart);
      setChartData(parsed);
    } catch (err) {
      message.error('加載圖表失敗');
    } finally {
      setLoading(false);
    }
  };

  if (!ticker) return <Empty description="請選擇股票" />;

  return (
    <Spin spinning={loading}>
      {chartData && chartData.data ? (
        <Plot
          data={chartData.data}
          layout={{
            ...chartData.layout,
            autosize: true,
            height: 800
          }}
          useResizeHandler
          style={{ width: '100%', height: '800px' }}
        />
      ) : null}
    </Spin>
  );
}
