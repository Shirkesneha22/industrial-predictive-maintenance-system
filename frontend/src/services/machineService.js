import apiClient from './api';

export const machineService = {
  /**
   * Fetch paginated list of machines with optional filtering.
   * @param {Object} params
   * @param {number} [params.page=1]
   * @param {number} [params.page_size=20]
   * @param {number} [params.line_id]
   * @param {string} [params.machine_type]
   * @param {boolean} [params.is_active]
   */
  async getMachines(params = {}) {
    return apiClient.get('/machines', { params });
  },

  /**
   * Fetch individual machine details including attached sensor topology.
   * @param {number|string} machineId
   */
  async getMachineById(machineId) {
    return apiClient.get(`/machines/${machineId}`);
  },

  /**
   * Assess machine health index (0-100) and risk score (0-100) at point-in-time cutoff.
   * @param {number|string} machineId
   * @param {string} [predictionTimestamp] ISO UTC string
   */
  async getMachineRisk(machineId, predictionTimestamp) {
    const params = predictionTimestamp ? { prediction_timestamp: predictionTimestamp } : {};
    return apiClient.get(`/machines/${machineId}/risk`, { params });
  },

  /**
   * Convenience alias for machine health condition assessment.
   * @param {number|string} machineId
   * @param {string} [predictionTimestamp] ISO UTC string
   */
  async getMachineHealth(machineId, predictionTimestamp) {
    const params = predictionTimestamp ? { prediction_timestamp: predictionTimestamp } : {};
    return apiClient.get(`/machines/${machineId}/health`, { params });
  },

  /**
   * Fetch historical maintenance work orders and failure events for a machine.
   * @param {number|string} machineId
   */
  async getMachineMaintenance(machineId) {
    return apiClient.get(`/machines/${machineId}/maintenance`);
  },
};

export default machineService;
