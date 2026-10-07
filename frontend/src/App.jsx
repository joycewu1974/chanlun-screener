import React, { useState } from 'react';
import { Layout, Tabs } from 'antd';
import StockList from './components/StockList';
import Chart from './components/Chart';
import AnalysisPanel from './components/AnalysisPanel';
import './index.css';

const { Header, Content, Footer } = Layout;

export default function App() {
  const [selectedTicker, setSelectedTicker] = useState(null);

  const tabs = [
    {
      key: '1',
      label: '📊 掃描清單',
      children: <StockList onSelectStock={setSelectedTicker} />
    },
    {
      key: '2',
      label: '📈 圖表分析',
      children: (
        <div style={{ padding: '20px' }}>
          <Chart ticker={selectedTicker} />
        </div>
      )
    },
    {
      key: '3',
      label: '🎯 詳細分析',
      children: <AnalysisPanel ticker={selectedTicker} />
    }
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{
        background: '#001529',
        color: 'white',
        padding: '0 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <h1 style={{ color: 'white', margin: 0 }}>🔮 纏論掃描系統</h1>
        <span style={{ color: '#ccc' }}>美股自動化選股系統</span>
      </Header>

      <Content style={{ padding: '20px', background: '#f0f2f5' }}>
        <Tabs items={tabs} type="card" />
      </Content>

      <Footer style={{ textAlign: 'center', background: '#001529', color: 'white' }}>
        纏論掃描系統 ©2024 | 基於Mark Minervini VCP × 李彪纏論理論
      </Footer>
    </Layout>
  );
}
