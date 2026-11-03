import apiClient from './api';

export const maintenanceService = {
  /**
   * Fetch aggregate maintenance overview stats (work orders, failures, downtime).
   */
  async getOverview() {
    return apiClient.get('/maintenance/overview');
  },

  /**
   * Fetch paginated list of work orders.
   * @param {Object} params
   * @param {number} [params.page=1]
   * @param {number} [params.page_size=20]
   * @param {number} [params.machine_id]
   * @param {string} [params.status]
   * @param {string} [params.work_type]
   */
  async getWorkOrders(params = {}) {
    return apiClient.get('/maintenance/work-orders', { params });
  },

  /**
   * Fetch paginated list of failure events.
   * @param {Object} params
   * @param {number} [params.page=1]
   * @param {number} [params.page_size=20]
   * @param {number} [params.machine_id]
   * @param {string} [params.failure_type]
   * @param {string} [params.severity]
   */
  async getFailures(params = {}) {
    return apiClient.get('/maintenance/failures', { params });
  },
};

export default maintenanceService;
