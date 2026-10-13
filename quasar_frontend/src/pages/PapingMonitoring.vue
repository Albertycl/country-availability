<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-lg">
      <div class="text-h4">Paping Monitoring</div>
      <q-space />
      <div class="text-body2 text-grey-7 bg-grey-1 q-pa-sm rounded-borders">
        <strong>Command:</strong> <code>paging -c 20 {destination} -p 443 --nocolor</code>
      </div>
    </div>
    
    <!-- Add New Paging Destination Form -->
    <q-card class="q-mb-lg">
      <q-card-section>
        <div class="text-h6">Add New Paging Destination</div>
      </q-card-section>
      
      <q-card-section>
        <div class="row q-gutter-sm">
          <div class="col-2">
            <q-input
              v-model="newDestination.destination"
              label="Destination"
              placeholder="192.168.1.1 or example.com"
              outlined
              dense
            />
          </div>
          
          <div class="col-1">
            <q-input
              v-model="newDestination.starting_time"
              label="Starting Time"
              outlined
              dense
            >
              <template v-slot:prepend>
                <q-icon name="access_time" class="cursor-pointer">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <q-time
                      v-model="newDestination.starting_time"
                      mask="HH:mm"
                      format24h
                    >
                      <div class="row items-center justify-end">
                        <q-btn v-close-popup label="Close" color="primary" flat />
                      </div>
                    </q-time>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>
          </div>
          
          <div class="col-1">
            <q-select
              v-model="newDestination.interval_minutes"
              :options="intervalOptions"
              label="Check Interval"
              outlined
              dense
              emit-value
              map-options
            />
          </div>
          
          <div class="col-1">
            <q-select
              v-model="newDestination.country"
              :options="countryOptions"
              label="Country"
              outlined
              dense
              emit-value
              map-options
            />
          </div>
          
          <div class="col-1">
            <q-input
              v-model="newDestination.packet_loss_threshold"
              label="Packet Loss Threshold (%)"
              outlined
              dense
              type="number"
              step="0.1"
              min="0"
              max="100"
            />
          </div>
          
          <div class="col-1">
            <q-input
              v-model="newDestination.latency_threshold"
              label="Latency Threshold (ms)"
              outlined
              dense
              type="number"
              step="1"
              min="0"
            />
          </div>
          
          <div class="col">
            <q-btn
              @click="addPagingDestination"
              color="primary"
              label="ADD DESTINATION"
              :disable="adding"
              dense
            />
          </div>
        </div>
      </q-card-section>
    </q-card>

    <!-- Currently Scheduled Destinations -->
    <q-card class="q-mb-lg">
      <q-card-section>
        <div class="text-h6">Currently Scheduled Destinations</div>
      </q-card-section>
      
      <!-- Filter Controls -->
      <q-card-section>
        <div class="row q-gutter-md">
          <q-input
            v-model="destinationFilters.destination"
            outlined
            dense
            placeholder="Filter by destination..."
            style="min-width: 200px"
            clearable
          >
            <template v-slot:prepend>
              <q-icon name="search" />
            </template>
          </q-input>
          
          <q-select
            v-model="destinationFilters.country"
            :options="[{label: 'All Countries', value: ''}, ...countryOptions]"
            outlined
            dense
            emit-value
            map-options
            style="min-width: 150px"
          />
          
          <q-input
            v-model="destinationFilters.minInterval"
            outlined
            dense
            placeholder="Min interval"
            type="number"
            style="min-width: 120px"
          />
          
          <q-input
            v-model="destinationFilters.maxInterval"
            outlined
            dense
            placeholder="Max interval"
            type="number"
            style="min-width: 120px"
          />
          
          <q-btn
            @click="clearFilters"
            icon="clear"
            label="CLEAR FILTERS"
            color="secondary"
            outline
            dense
          />
          
          <q-btn
            @click="refreshAllData"
            icon="refresh"
            label="REFRESH DATA"
            color="primary"
            outline
            dense
            :loading="loadingDestinations || loadingAlerts || loadingTestSummary"
          />
        </div>
      </q-card-section>
      
      <q-card-section>
        <q-table
          :rows="filteredDestinations"
          :columns="destinationColumns"
          row-key="id"
          :loading="loadingDestinations"
          :pagination="destinationPagination"
        >
          <template v-slot:body-cell-status="props">
            <q-td :props="props">
              <q-badge
                :color="props.row.is_active ? 'green' : 'red'"
                :label="props.row.is_active ? 'Active' : 'Inactive'"
              />
            </q-td>
          </template>
          
          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <q-btn
                @click="manualCheck(props.row.id)"
                icon="refresh"
                color="primary"
                size="sm"
                flat
                round
                :loading="props.row.checking"
              >
                <q-tooltip>Manual Check</q-tooltip>
              </q-btn>
              <q-btn
                @click="deleteDestination(props.row.id)"
                icon="delete"
                color="red"
                size="sm"
                flat
                round
              >
                <q-tooltip>Delete</q-tooltip>
              </q-btn>
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>

    <!-- Paging Alerts Table -->
    <q-card class="q-mb-lg">
      <q-card-section>
        <div class="text-h6">Paging Alerts (Custom Thresholds)</div>
      </q-card-section>
      
      <q-card-section>
        <q-table
          :rows="pagingAlerts"
          :columns="alertColumns"
          row-key="id"
          :loading="loadingAlerts"
          :pagination="alertPagination"
        >
          <template v-slot:body-cell-packet_loss="props">
            <q-td :props="props">
              <q-badge
                :color="props.row.alert_triggered ? 'red' : 'green'"
                :label="props.row.packet_loss_percentage.toFixed(1) + '%'"
              />
            </q-td>
          </template>
          
          <template v-slot:body-cell-latency="props">
            <q-td :props="props">
              <q-badge
                :color="props.row.alert_triggered ? 'red' : 'green'"
                :label="props.row.avg_latency_ms.toFixed(1) + 'ms'"
              />
            </q-td>
          </template>
          
          <template v-slot:body-cell-alert_reason="props">
            <q-td :props="props">
              <span v-if="props.row.alert_triggered">
                Threshold Exceeded
              </span>
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>

    <!-- Paging Test Summary Table -->
    <q-card>
      <q-card-section>
        <div class="text-h6">Paging Test Summary Statistics</div>
      </q-card-section>
      
      <q-card-section>
        <q-table
          :rows="pagingTestSummary"
          :columns="summaryColumns"
          row-key="id"
          :loading="loadingTestSummary"
          :pagination="summaryPagination"
        >
          <template v-slot:body-cell-summary="props">
            <q-td :props="props">
              <div class="text-weight-medium">
                Attempted={{ props.row.attempted }}, Connected={{ props.row.connected }}, Failed={{ props.row.failed }} ({{ props.row.packet_loss_percentage.toFixed(2) }}%)
              </div>
            </q-td>
          </template>
          
          <template v-slot:body-cell-latency="props">
            <q-td :props="props">
              <div class="text-weight-medium">
                Min={{ props.row.min_latency_ms.toFixed(2) }}ms, Max={{ props.row.max_latency_ms.toFixed(2) }}ms, Avg={{ props.row.avg_latency_ms.toFixed(2) }}ms
              </div>
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useQuasar } from 'quasar'
import axios from 'axios'

export default {
  name: 'PapingMonitoring',
  setup() {
    const $q = useQuasar()
    
    // Reactive data
    const loadingDestinations = ref(false)
    const loadingAlerts = ref(false)
    const loadingTestSummary = ref(false)
    const adding = ref(false)
    const scheduledDestinations = ref([])
    const pagingAlerts = ref([])
    const pagingTestSummary = ref([])
    const refreshInterval = ref(null)
    const timeUpdateInterval = ref(null)
    
    const newDestination = reactive({
      destination: '',
      starting_time: new Date().toLocaleTimeString('en-GB', { 
        hour: '2-digit', 
        minute: '2-digit',
        timeZone: 'Asia/Shanghai'
      }),
      interval_minutes: 5,
      country: 'Korea',
      packet_loss_threshold: 0,
      latency_threshold: 10
    })
    
    const destinationFilters = reactive({
      destination: '',
      country: '',
      minInterval: '',
      maxInterval: ''
    })
    
    // Options
    const intervalOptions = [
      { label: '1 minute', value: 1 },
      { label: '5 minutes', value: 5 },
      { label: '10 minutes', value: 10 },
      { label: '30 minutes', value: 30 },
      { label: '60 minutes', value: 60 }
    ]
    
    const countryOptions = [
      { label: 'China', value: 'China' },
      { label: 'Vietnam', value: 'Vietnam' },
      { label: 'Indonesia', value: 'Indonesia' },
      { label: 'Thailand', value: 'Thailand' },
      { label: 'Malaysia', value: 'Malaysia' },
      { label: 'Cambodia', value: 'Cambodia' },
      { label: 'Korea', value: 'KR' }
    ]
    
    // Table columns
    const destinationColumns = [
      { name: 'destination', label: 'Destination', field: 'destination', align: 'left', sortable: true },
      { name: 'interval', label: 'Interval (min)', field: 'interval_minutes', align: 'center', sortable: true },
      { name: 'country', label: 'Country', field: 'country', align: 'center' },
      { name: 'packet_loss_threshold', label: 'Packet Loss Thresh...', field: 'packet_loss_threshold', align: 'center', sortable: true },
      { name: 'latency_threshold', label: 'Latency Threshold (ms)', field: 'latency_threshold', align: 'center', sortable: true },
      { name: 'starting_time', label: 'Starting Time', field: 'starting_time', align: 'center' },
      { name: 'last_checked', label: 'Last Checked', field: 'last_checked_at', align: 'center' },
      { name: 'next_check', label: 'Next Check Time', field: 'next_check_time', align: 'center' },
      { name: 'status', label: 'Status', field: 'is_active', align: 'center' },
      { name: 'actions', label: 'Actions', field: 'actions', align: 'center' }
    ]
    
    const alertColumns = [
      { name: 'destination', label: 'Destination', field: 'destination', align: 'left', sortable: true },
      { name: 'hostname', label: 'Hostname', field: 'hostname', align: 'center' },
      { name: 'probe_name', label: 'Probe IP', field: 'probe_ip', align: 'center' },
      { name: 'country', label: 'Country', field: 'country', align: 'center' },
      { name: 'packet_loss', label: 'Packet Loss', field: 'packet_loss_percentage', align: 'center', sortable: true },
      { name: 'latency', label: 'Avg Latency', field: 'avg_latency_ms', align: 'center', sortable: true },
      { name: 'alert_reason', label: 'Alert Reason', field: 'alert_reason', align: 'center' },
      { name: 'checked_at', label: 'Timestamp', field: 'checked_at', align: 'center', sortable: true }
    ]
    
    const summaryColumns = [
      { name: 'destination', label: 'Destination', field: 'destination', align: 'left', sortable: true },
      { name: 'hostname', label: 'Hostname', field: 'hostname', align: 'center' },
      { name: 'probe_name', label: 'Probe IP', field: 'probe_ip', align: 'center' },
      { name: 'country', label: 'Country', field: 'country', align: 'center' },
      { name: 'summary', label: 'Test Summary', field: 'summary', align: 'left' },
      { name: 'latency', label: 'Latency Statistics', field: 'latency', align: 'left' },
      { name: 'checked_at', label: 'Timestamp', field: 'checked_at', align: 'center', sortable: true }
    ]
    
    // Pagination - Set to 0 to show all rows without pagination
    const destinationPagination = reactive({
      rowsPerPage: 0
    })
    
    const alertPagination = reactive({
      rowsPerPage: 0
    })
    
    const summaryPagination = reactive({
      rowsPerPage: 0
    })
    
    // Computed properties
    const filteredDestinations = computed(() => {
      let filtered = scheduledDestinations.value
      
      if (destinationFilters.destination) {
        filtered = filtered.filter(dest => 
          dest.destination.toLowerCase().includes(destinationFilters.destination.toLowerCase())
        )
      }
      
      if (destinationFilters.country) {
        filtered = filtered.filter(dest => dest.country === destinationFilters.country)
      }
      
      if (destinationFilters.minInterval) {
        filtered = filtered.filter(dest => dest.interval_minutes >= parseInt(destinationFilters.minInterval))
      }
      
      if (destinationFilters.maxInterval) {
        filtered = filtered.filter(dest => dest.interval_minutes <= parseInt(destinationFilters.maxInterval))
      }
      
      return filtered
    })
    
    // API methods
    const fetchDestinations = async () => {
      try {
        console.log('[PAPING MONITORING] Starting to fetch destinations...')
        loadingDestinations.value = true
        const response = await axios.get('http://localhost:5030/paping/api/paping-destinations')
        console.log('[PAGING MONITORING] Received destinations response:', response.data)
        scheduledDestinations.value = response.data.map(dest => ({
          ...dest,
          checking: false
        }))
        console.log('[PAGING MONITORING] Updated scheduledDestinations:', scheduledDestinations.value)
      } catch (error) {
        console.error('[PAGING MONITORING] Error fetching destinations:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to fetch destinations'
        })
      } finally {
        console.log('[PAGING MONITORING] Setting loadingDestinations to false')
        loadingDestinations.value = false
      }
    }
    
    const fetchAlerts = async () => {
      try {
        console.log('[PAGING MONITORING] Starting to fetch alerts...')
        loadingAlerts.value = true
        const response = await axios.get('http://localhost:5030/paping/api/paping-alerts')
        console.log('[PAGING MONITORING] Received alerts response:', response.data)
        pagingAlerts.value = response.data
        console.log('[PAGING MONITORING] Updated pagingAlerts:', pagingAlerts.value)
      } catch (error) {
        console.error('[PAGING MONITORING] Error fetching alerts:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to fetch alerts'
        })
      } finally {
        console.log('[PAGING MONITORING] Setting loadingAlerts to false')
        loadingAlerts.value = false
      }
    }
    
    const fetchTestSummary = async () => {
      try {
        console.log('[PAGING MONITORING] Starting to fetch test summary...')
        loadingTestSummary.value = true
        const response = await axios.get('http://localhost:5030/paping/api/paping-test-summary')
        console.log('[PAGING MONITORING] Received test summary response:', response.data)
        pagingTestSummary.value = response.data
        console.log('[PAGING MONITORING] Updated pagingTestSummary:', pagingTestSummary.value)
      } catch (error) {
        console.error('[PAGING MONITORING] Error fetching test summary:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to fetch test summary'
        })
      } finally {
        console.log('[PAGING MONITORING] Setting loadingTestSummary to false')
        loadingTestSummary.value = false
      }
    }
    
    const addPagingDestination = async () => {
      console.log('[PAGING MONITORING] ADD DESTINATION button clicked')
      console.log('[PAGING MONITORING] Current form data:', newDestination)
      
      if (!newDestination.destination) {
        console.log('[PAGING MONITORING] Validation failed - no destination provided')
        $q.notify({
          type: 'warning',
          message: 'Please enter a destination'
        })
        return
      }
      
      try {
        console.log('[PAGING MONITORING] Starting to add destination...')
        adding.value = true
        const response = await axios.post('http://localhost:5030/paping/api/paping-destinations', newDestination)
        console.log('[PAGING MONITORING] Add destination response:', response.data)
        
        if (response.data.success) {
          const addedDestination = newDestination.destination
          const newDestinationId = response.data.destination_id
          
          $q.notify({
            type: 'positive',
            message: `Added paging destination: ${addedDestination}. Running immediate test...`
          })
          
          // Reset form first
          newDestination.destination = ''
          // Keep current time, don't reset to hardcoded value
          newDestination.interval_minutes = 5
          newDestination.country = 'Korea'
          newDestination.packet_loss_threshold = 0
          newDestination.latency_threshold = 10
          
          // Refresh destinations
          await fetchDestinations()
          
          // Trigger immediate test for the newly added destination
          if (newDestinationId) {
            console.log('[PAGING MONITORING] Triggering immediate test for new destination ID:', newDestinationId)
            try {
              const testResponse = await axios.post(`http://localhost:5030/paping/api/manual-paping-check/${newDestinationId}`)
              if (testResponse.data.success) {
                $q.notify({
                  type: 'info',
                  message: `Immediate test completed for ${addedDestination}`
                })
                // Refresh all data to show test results
                await Promise.all([fetchDestinations(), fetchAlerts(), fetchTestSummary()])
              }
            } catch (testError) {
              console.error('[PAGING MONITORING] Error running immediate test:', testError)
              $q.notify({
                type: 'warning',
                message: `Added ${addedDestination} but immediate test failed`
              })
            }
          }
        }
      } catch (error) {
        console.error('Error adding destination:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to add destination'
        })
      } finally {
        adding.value = false
      }
    }
    
    const deleteDestination = async (destinationId) => {
      try {
        const response = await axios.delete(`http://localhost:5030/paping/api/paping-destinations/${destinationId}`)
        
        if (response.data.success) {
          $q.notify({
            type: 'positive',
            message: 'Destination deleted successfully'
          })
          await fetchDestinations()
        }
      } catch (error) {
        console.error('Error deleting destination:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to delete destination'
        })
      }
    }
    
    const manualCheck = async (destinationId) => {
      const destination = scheduledDestinations.value.find(d => d.id === destinationId)
      if (!destination) return
      
      try {
        destination.checking = true
        const response = await axios.post(`http://localhost:5030/paping/api/manual-paping-check/${destinationId}`)
        
        if (response.data.success) {
          $q.notify({
            type: 'positive',
            message: response.data.message || 'Manual check completed'
          })
          // Refresh data immediately after test
          console.log('[PAGING MONITORING] Refreshing all data after manual test...')
          await Promise.all([fetchDestinations(), fetchAlerts(), fetchTestSummary()])
          console.log('[PAGING MONITORING] Data refresh completed')
        } else {
          $q.notify({
            type: 'warning',
            message: response.data.message || 'Manual check failed'
          })
        }
      } catch (error) {
        console.error('Error performing manual check:', error)
        $q.notify({
          type: 'negative',
          message: 'Manual check failed'
        })
      } finally {
        destination.checking = false
      }
    }
    
    const clearFilters = () => {
      destinationFilters.destination = ''
      destinationFilters.country = ''
      destinationFilters.minInterval = ''
      destinationFilters.maxInterval = ''
    }
    
    const refreshAllData = async () => {
      console.log('[PAGING MONITORING] Manual refresh button clicked')
      try {
        await Promise.all([fetchDestinations(), fetchAlerts(), fetchTestSummary()])
        $q.notify({
          type: 'positive',
          message: 'Data refreshed successfully'
        })
        console.log('[PAGING MONITORING] Manual data refresh completed')
      } catch (error) {
        console.error('[PAGING MONITORING] Error during manual refresh:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to refresh data'
        })
      }
    }
    
    const startAutoRefresh = () => {
      refreshInterval.value = setInterval(async () => {
        await Promise.all([fetchDestinations(), fetchAlerts(), fetchTestSummary()])
      }, 30000) // Refresh every 30 seconds
    }
    
    const startTimeAutoUpdate = () => {
      timeUpdateInterval.value = setInterval(() => {
        newDestination.starting_time = new Date().toLocaleTimeString('en-GB', {
          hour: '2-digit',
          minute: '2-digit', 
          timeZone: 'Asia/Shanghai'
        })
      }, 1000) // Update every second
    }
    
    const stopAutoRefresh = () => {
      if (refreshInterval.value) {
        clearInterval(refreshInterval.value)
        refreshInterval.value = null
      }
    }
    
    const stopTimeAutoUpdate = () => {
      if (timeUpdateInterval.value) {
        clearInterval(timeUpdateInterval.value)
        timeUpdateInterval.value = null
      }
    }
    
    // Lifecycle
    onMounted(async () => {
      console.log('[PAGING MONITORING] Component mounted, starting data fetch...')
      await Promise.all([fetchDestinations(), fetchAlerts(), fetchTestSummary()])
      console.log('[PAGING MONITORING] Initial data fetch completed')
      startAutoRefresh()
      startTimeAutoUpdate()
      console.log('[PAGING MONITORING] Auto-refresh and time update started')
    })
    
    onBeforeUnmount(() => {
      stopAutoRefresh()
      stopTimeAutoUpdate()
    })
    
    return {
      // Data
      loadingDestinations,
      loadingAlerts,
      loadingTestSummary,
      adding,
      scheduledDestinations,
      pagingAlerts,
      pagingTestSummary,
      newDestination,
      destinationFilters,
      
      // Options
      intervalOptions,
      countryOptions,
      
      // Table config
      destinationColumns,
      alertColumns,
      summaryColumns,
      destinationPagination,
      alertPagination,
      summaryPagination,
      
      // Computed
      filteredDestinations,
      
      // Methods
      addPagingDestination,
      deleteDestination,
      manualCheck,
      clearFilters,
      refreshAllData
    }
  }
}
</script>

<style scoped>
.q-table th {
  font-weight: bold;
}

.q-badge {
  font-weight: 500;
}
</style>