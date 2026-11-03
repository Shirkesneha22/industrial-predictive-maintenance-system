-- Deliberate Edge-Case Anomalies for Data Quality Validation

-- Telemetry Anomalies (30 rows)
-- Anomaly: ANOM-0001
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-UNKNOWN-9001'), '2026-09-15T12:00:00+00:00', 10.8367, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0002
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-UNKNOWN-9002'), '2026-09-15T14:00:00+00:00', 9.5307, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0003
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-UNKNOWN-9003'), '2026-09-15T16:00:00+00:00', 13.1005, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0004
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-UNKNOWN-9004'), '2026-09-15T18:00:00+00:00', 2.6307, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0005
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-UNKNOWN-9005'), '2026-09-15T20:00:00+00:00', 12.7069, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0006
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-UNKNOWN-9006'), '2026-09-15T22:00:00+00:00', 4.9958, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0007
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-UNKNOWN-9007'), '2026-09-16T00:00:00+00:00', 2.038, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0008
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-UNKNOWN-9008'), '2026-09-16T02:00:00+00:00', 12.7315, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0009
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-UNKNOWN-9009'), '2026-09-16T04:00:00+00:00', 3.7117, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0010
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-UNKNOWN-9010'), '2026-09-16T06:00:00+00:00', 4.5851, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0011
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-001-002-VIB-01'), '2026-09-16T14:00:00+00:00', 9999.0, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0012
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-001-003-TEMP-01'), '2026-09-17T14:00:00+00:00', -999.0, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0013
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-001-004-VIB-01'), '2026-09-18T14:00:00+00:00', 8500.5, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0014
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-001-005-TEMP-01'), '2026-09-19T14:00:00+00:00', -450.0, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0015
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-001-006-VIB-01'), '2026-09-20T14:00:00+00:00', 12000.0, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0016
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-001-007-TEMP-01'), '2026-09-21T14:00:00+00:00', -800.0, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0017
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-001-008-VIB-01'), '2026-09-22T14:00:00+00:00', 9500.0, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0018
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-001-001-TEMP-01'), '2026-09-23T14:00:00+00:00', -600.0, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0019
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-001-002-VIB-01'), '2026-09-24T14:00:00+00:00', 15000.0, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0020
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-001-003-TEMP-01'), '2026-09-25T14:00:00+00:00', -1000.0, 'invalid', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0041
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-002-002-PRS-01'), '2026-10-16T18:00:00+00:00', 0.0, 'ok', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0042
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-002-003-PRS-01'), '2026-10-17T18:00:00+00:00', 0.0, 'ok', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0043
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-002-004-PRS-01'), '2026-10-18T18:00:00+00:00', 0.0, 'ok', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0044
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-002-005-PRS-01'), '2026-10-19T18:00:00+00:00', 0.0, 'ok', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0045
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-002-006-PRS-01'), '2026-10-20T18:00:00+00:00', 0.0, 'ok', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0046
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-002-007-PRS-01'), '2026-10-21T18:00:00+00:00', 0.0, 'ok', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0047
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-002-008-PRS-01'), '2026-10-22T18:00:00+00:00', 0.0, 'ok', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0048
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-002-001-PRS-01'), '2026-10-23T18:00:00+00:00', 0.0, 'ok', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0049
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-002-002-PRS-01'), '2026-10-24T18:00:00+00:00', 0.0, 'ok', NOW()) ON CONFLICT DO NOTHING;
-- Anomaly: ANOM-0050
INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='SNS-MCH-LINE-PLT-001-002-003-PRS-01'), '2026-10-25T18:00:00+00:00', 0.0, 'ok', NOW()) ON CONFLICT DO NOTHING;

