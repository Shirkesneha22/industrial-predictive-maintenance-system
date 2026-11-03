import apiClient from './api';

export const telemetryService = {
  /**
   * Query historical sensor telemetry with pagination and filtering.
   * @param {Object} params
   * @param {number} [params.page=1]
   * @param {number} [params.page_size=100]
   * @param {number} [params.machine_id]
   * @param {number} [params.sensor_id]
   * @param {string} [params.sensor_type]
   * @param {string} [params.quality_status] 'normal' | 'sensor_fault' | 'invalid' | 'missing'
   * @param {string} [params.start_time] ISO UTC string
   * @param {string} [params.end_time] ISO UTC string
   */
  async getHistoricalTelemetry(params = {}) {
    return apiClient.get('/telemetry', { params });
  },

  /**
   * Fetch the single most recent telemetry event recorded for each mounted sensor on a machine.
   * @param {number|string} machineId
   */
  async getLatestTelemetry(machineId) {
    return apiClient.get('/telemetry/latest', {
      params: { machine_id: machineId },
    });
  },

  /**
   * Shortcut to query historical telemetry for a specific machine.
   * @param {number|string} machineId
   * @param {Object} params
   */
  async getMachineTelemetry(machineId, params = {}) {
    return apiClient.get(`/telemetry/machines/${machineId}`, { params });
  },

  /**
   * Efficiently aggregates reading counts by quality status across the database
   * without fetching all records, by querying the paginated endpoint with page_size=1.
   */
  async getDataQualityCounts() {
    const [totalRes, normalRes, faultRes, invalidRes, missingRes] = await Promise.all([
      apiClient.get('/telemetry', { params: { page_size: 1, page: 1 } }),
      apiClient.get('/telemetry', { params: { quality_status: 'normal', page_size: 1, page: 1 } }),
      apiClient.get('/telemetry', { params: { quality_status: 'sensor_fault', page_size: 1, page: 1 } }),
      apiClient.get('/telemetry', { params: { quality_status: 'invalid', page_size: 1, page: 1 } }),
      apiClient.get('/telemetry', { params: { quality_status: 'missing', page_size: 1, page: 1 } }),
    ]);

    const total = totalRes?.total || 0;
    const normal = normalRes?.total || 0;
    const sensor_fault = faultRes?.total || 0;
    const invalid = invalidRes?.total || 0;
    const missing = missingRes?.total || 0;

    return {
      total,
      normal,
      sensor_fault,
      invalid,
      missing,
      normalRate: total > 0 ? (normal / total) * 100 : 0,
      faultRate: total > 0 ? (sensor_fault / total) * 100 : 0,
      invalidRate: total > 0 ? (invalid / total) * 100 : 0,
      missingRate: total > 0 ? (missing / total) * 100 : 0,
    };
  },
};

export default telemetryService;
