import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Spin, message, Descriptions, Tag } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { stockApi } from '../api';

export default function AnalysisPanel({ ticker }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!ticker) return;
    loadAnalysis();
  }, [ticker]);

  const loadAnalysis = async () => {
    setLoading(true);
    try {
      const { data } = await stockApi.analyzeStock(ticker);
      setAnalysis(data);
    } catch (err) {
      message.error('加載分析失敗');
    } finally {
      setLoading(false);
    }
  };

  if (!ticker || !analysis) return null;

  const priceChange = (analysis.entry_price - analysis.current_price) / analysis.current_price;
  const gainTo10 = (analysis.target_10pct - analysis.entry_price) / analysis.entry_price;
  const gainTo20 = (analysis.target_20pct - analysis.entry_price) / analysis.entry_price;

  return (
    <Spin spinning={loading}>
      <div style={{ padding: '20px' }}>
        <Card title={`${ticker} - 纏論分析`}>
          <Row gutter={16} style={{ marginBottom: '20px' }}>
            <Col xs={12} sm={6}>
              <Statistic
                title="現價"
                value={analysis.current_price}
                prefix="$"
                precision={2}
              />
            </Col>
            <Col xs={12} sm={6}>
              <Statistic
                title="訊號"
                value={analysis.signal_type || '無'}
                valueStyle={{ color: analysis.signal_type ? '#3f8600' : '#d4380d' }}
              />
            </Col>
            <Col xs={12} sm={6}>
              <Statistic
                title="確信度"
                value={analysis.confidence}
                valueStyle={{ color: analysis.confidence === 'HIGH' ? '#3f8600' : '#faad14' }}
              />
            </Col>
            <Col xs={12} sm={6}>
              <Statistic
                title="波動率 (ATR)"
                value={analysis.atr}
                prefix="$"
                precision={2}
              />
            </Col>
          </Row>

          <Descriptions title="進出場點位" column={1} style={{ marginBottom: '20px' }}>
            <Descriptions.Item label="進場價">
              <strong>${analysis.entry_price.toFixed(2)}</strong>
              <span style={{ marginLeft: '10px', color: '#999' }}>
                ({priceChange > 0 ? '+' : ''}{(priceChange * 100).toFixed(2)}%)
              </span>
            </Descriptions.Item>
            <Descriptions.Item label="支撐位">
              <strong style={{ color: '#d4380d' }}>${analysis.support.toFixed(2)}</strong>
            </Descriptions.Item>
            <Descriptions.Item label="10%目標">
              <strong style={{ color: '#faad14' }}>${analysis.target_10pct.toFixed(2)}</strong>
              <span style={{ marginLeft: '10px', color: '#666' }}>
                +{(gainTo10 * 100).toFixed(2)}%
              </span>
            </Descriptions.Item>
            <Descriptions.Item label="20%目標">
              <strong style={{ color: '#3f8600' }}>${analysis.target_20pct.toFixed(2)}</strong>
              <span style={{ marginLeft: '10px', color: '#666' }}>
                +{(gainTo20 * 100).toFixed(2)}%
              </span>
            </Descriptions.Item>
          </Descriptions>

          <div style={{ marginBottom: '20px' }}>
            <h4>訊號描述</h4>
            <p>{analysis.description}</p>
          </div>

          {analysis.centers && analysis.centers.length > 0 && (
            <div>
              <h4>中樞信息</h4>
              {analysis.centers.map((center, idx) => (
                <Card key={idx} size="small" style={{ marginBottom: '10px' }}>
                  <Row gutter={16}>
                    <Col xs={12} sm={6}>
                      <Statistic title="下界" value={center.low} prefix="$" />
                    </Col>
                    <Col xs={12} sm={6}>
                      <Statistic title="上界" value={center.high} prefix="$" />
                    </Col>
                    <Col xs={12} sm={6}>
                      <Statistic title="寬度" value={center.width} prefix="$" />
                    </Col>
                    <Col xs={12} sm={6}>
                      <Statistic title="中點" value={center.midpoint} prefix="$" />
                    </Col>
                  </Row>
                </Card>
              ))}
            </div>
          )}
        </Card>
      </div>
    </Spin>
  );
}
