import React, { useState, useEffect } from 'react';
import { 
  Table, Button, Space, Tag, Spin, message, Empty, Select, Tooltip,
  Progress, Statistic, Row, Col, Card
} from 'antd';
import { ReloadOutlined, DownloadOutlined, FilterOutlined } from '@ant-design/icons';
import { stockApi } from '../api';

export default function StockList({ onSelectStock }) {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [signalFilter, setSignalFilter] = useState(null);
  const [confidenceFilter, setConfidenceFilter] = useState(null);
  const [scanStatus, setScanStatus] = useState(null);

  useEffect(() => {
    loadResults();
    const interval = setInterval(() => {
      checkProgress();
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const checkProgress = async () => {
    try {
      const { data } = await stockApi.getScanStatus();
      setScanStatus(data);
      
      if (data.scanning) {
        setScanning(true);
      } else if (scanning) {
        setScanning(false);
        await loadResults();
        message.success(`✅ 掃描完成！找到 ${data.signals_found} 個訊號`);
      }
    } catch (err) {
      console.error('Failed to check progress', err);
    }
  };

  const loadResults = async () => {
    setLoading(true);
    try {
      const { data } = await stockApi.getScanResults(signalFilter, confidenceFilter, 100);
      setResults(data.data || []);
    } catch (err) {
      message.error('加載結果失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleRunScan = async () => {
    try {
      await stockApi.runScan();
      setScanning(true);
      message.info('🔍 掃描已啟動...');
    } catch (err) {
      message.error('啟動掃描失敗');
    }
  };

  const columns = [
    {
      title: '股票',
      dataIndex: 'ticker',
      key: 'ticker',
      width: 80,
      fixed: 'left',
      sorter: (a, b) => a.ticker.localeCompare(b.ticker),
    },
    {
      title: '現價',
      dataIndex: 'current_price',
      key: 'current_price',
      width: 90,
      sorter: (a, b) => a.current_price - b.current_price,
      render: price => `$${price.toFixed(2)}`
    },
    {
      title: '訊號',
      dataIndex: 'signal_type',
      key: 'signal_type',
      width: 80,
      render: (text) => {
        const colorMap = { '一買': 'red', '二買': 'orange', '三買': 'green' };
        return <Tag color={colorMap[text] || 'blue'}>{text}</Tag>;
      }
    },
    {
      title: '確信度',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 80,
      render: (confidence) => {
        const colorMap = { 'HIGH': 'green', 'MEDIUM': 'orange', 'LOW': 'red' };
        return <Tag color={colorMap[confidence] || 'default'}>{confidence}</Tag>;
      }
    },
    {
      title: '進場點',
      dataIndex: 'entry_price',
      key: 'entry_price',
      width: 90,
      render: price => `$${price.toFixed(2)}`
    },
    {
      title: '支撐',
      dataIndex: 'support',
      key: 'support',
      width: 90,
      render: price => `$${price.toFixed(2)}`
    },
    {
      title: '10%目標',
      dataIndex: 'target_10pct',
      key: 'target_10pct',
      width: 100,
      render: price => `$${price.toFixed(2)}`
    },
    {
      title: '20%目標',
      dataIndex: 'target_20pct',
      key: 'target_20pct',
      width: 100,
      render: price => `$${price.toFixed(2)}`
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      fixed: 'right',
      render: (_, record) => (
        <Button 
          type="primary" 
          size="small"
          onClick={() => onSelectStock(record.ticker)}
        >
          查看
        </Button>
      )
    }
  ];

  return (
    <div style={{ padding: '20px' }}>
      {scanStatus && (
        <Card style={{ marginBottom: '20px', background: '#f6f8fb' }}>
          <Row gutter={16}>
            <Col xs={12} sm={6}>
              <Statistic 
                title="找到的訊號"
                value={scanStatus.signals_found}
                valueStyle={{ color: '#3f8600' }}
              />
            </Col>
            <Col xs={12} sm={6}>
              <Statistic 
                title="一買"
                value={scanStatus.summary?.by_type?.['一買'] || 0}
              />
            </Col>
            <Col xs={12} sm={6}>
              <Statistic 
                title="二買"
                value={scanStatus.summary?.by_type?.['二買'] || 0}
              />
            </Col>
            <Col xs={12} sm={6}>
              <Statistic 
                title="三買"
                value={scanStatus.summary?.by_type?.['三買'] || 0}
              />
            </Col>
          </Row>
          
          {scanning && (
            <Progress 
              percent={scanStatus.progress || 0}
              status="active"
              style={{ marginTop: '15px' }}
            />
          )}
        </Card>
      )}

      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <Button 
          type="primary" 
          icon={<ReloadOutlined />}
          onClick={handleRunScan}
          loading={scanning}
          size="large"
        >
          {scanning ? '掃描中...' : '🔍 立即掃描'}
        </Button>

        <Select
          placeholder="篩選訊號"
          style={{ width: 120 }}
          allowClear
          value={signalFilter}
          onChange={(val) => {
            setSignalFilter(val);
          }}
          options={[
            { label: '一買', value: '一買' },
            { label: '二買', value: '二買' },
            { label: '三買', value: '三買' }
          ]}
        />

        <Select
          placeholder="確信度"
          style={{ width: 120 }}
          allowClear
          value={confidenceFilter}
          onChange={(val) => {
            setConfidenceFilter(val);
          }}
          options={[
            { label: 'HIGH', value: 'HIGH' },
            { label: 'MEDIUM', value: 'MEDIUM' },
            { label: 'LOW', value: 'LOW' }
          ]}
        />

        <Button 
          onClick={() => {
            loadResults();
          }}
        >
          應用篩選
        </Button>

        <Button 
          icon={<DownloadOutlined />}
          onClick={() => {
            const csv = convertToCSV(results);
            downloadCSV(csv, `chanlun_signals_${new Date().toISOString().split('T')[0]}.csv`);
          }}
        >
          導出 CSV
        </Button>

        <span style={{ marginLeft: 'auto', color: '#666', alignSelf: 'center' }}>
          📊 共 {results.length} 個訊號
        </span>
      </div>

      <Spin spinning={loading}>
        {results.length === 0 ? (
          <Empty 
            description={scanning ? "掃描中，請稍候..." : "暫無訊號"} 
          />
        ) : (
          <Table
            dataSource={results}
            columns={columns}
            rowKey="ticker"
            pagination={{ pageSize: 20, position: ['bottomCenter'] }}
            scroll={{ x: 1200 }}
            size="small"
          />
        )}
      </Spin>
    </div>
  );
}

function convertToCSV(data) {
  const headers = ['股票', '現價', '訊號', '確信度', '進場點', '支撐', '10%目標', '20%目標'];
  const rows = data.map(r => [
    r.ticker,
    r.current_price,
    r.signal_type,
    r.confidence,
    r.entry_price,
    r.support,
    r.target_10pct,
    r.target_20pct
  ]);
  
  return [
    headers.join(','),
    ...rows.map(r => r.map(cell => `"${cell}"`).join(','))
  ].join('\n');
}

function downloadCSV(csv, filename) {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
}
