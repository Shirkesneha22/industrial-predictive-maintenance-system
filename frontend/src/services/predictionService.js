import apiClient from './api';

export const predictionService = {
  /**
   * Evaluate fleet-wide anomalies, machine health indices, and risk distribution.
   * @param {Object} params
   * @param {number} [params.page=1]
   * @param {number} [params.page_size=20]
   * @param {number} [params.line_id]
   * @param {string} [params.risk_level] 'Normal' | 'Warning' | 'Critical'
   * @param {boolean} [params.has_anomaly_only]
   * @param {string} [params.prediction_timestamp] ISO UTC string
   */
  async getFleetAnomalies(params = {}) {
    return apiClient.get('/predictions/fleet-anomalies', { params });
  },

  /**
   * Retrieve point-in-time risk assessment for a specific machine under predictions router.
   * @param {number|string} machineId
   * @param {string} [predictionTimestamp] ISO UTC string
   */
  async getMachineRisk(machineId, predictionTimestamp) {
    const params = predictionTimestamp ? { prediction_timestamp: predictionTimestamp } : {};
    return apiClient.get(`/predictions/machines/${machineId}/risk`, { params });
  },

  /**
   * Retrieve Remaining Useful Life (RUL) estimation with anti-leakage guarantee.
   * @param {number|string} machineId
   * @param {string} [predictionTimestamp] ISO UTC string
   */
  async getMachineRul(machineId, predictionTimestamp) {
    const params = predictionTimestamp ? { prediction_timestamp: predictionTimestamp } : {};
    return apiClient.get(`/predictions/machines/${machineId}/rul`, { params });
  },
};

export default predictionService;
