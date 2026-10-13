<template>
  <q-page class="q-pa-md">
    <div class="text-h4 q-mb-lg">Scheduled Domain Monitoring</div>
    
    <!-- Add New Scheduled Domain Form -->
    <q-card class="q-mb-lg">
      <q-card-section>
        <div class="text-h6">Add New Scheduled Domain</div>
      </q-card-section>
      
      <q-card-section>
        <div class="row q-gutter-md">
          <div class="col-12 col-md-3">
            <q-input
              v-model="newDomain.domain_name"
              label="Domain Name"
              placeholder="example.com"
              outlined
              dense
            />
          </div>
          
          <div class="col-12 col-md-2">
            <q-input
              v-model="newDomain.starting_time"
              label="Starting Time"
              outlined
              dense
            >
              <template v-slot:prepend>
                <q-icon name="access_time" class="cursor-pointer">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <q-time
                      v-model="newDomain.starting_time"
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
          
          <div class="col-12 col-md-2">
            <q-select
              v-model="newDomain.interval_minutes"
              :options="intervalOptions"
              label="Check Interval"
              outlined
              dense
              emit-value
              map-options
            />
          </div>
          
          <div class="col-12 col-md-2">
            <q-select
              v-model="newDomain.country"
              :options="countryOptions"
              label="Country"
              outlined
              dense
              emit-value
              map-options
            />
          </div>
          
          <div class="col-12 col-md-2">
            <q-select
              v-model="newDomain.domain_prefix"
              :options="prefixOptions"
              label="Domain Prefix"
              outlined
              dense
              emit-value
              map-options
            />
          </div>
          
          <div class="col-12 col-md-1">
            <q-btn
              @click="addScheduledDomain"
              color="primary"
              label="Add Domain"
              :disable="adding"
              dense
            />
          </div>
        </div>
      </q-card-section>
    </q-card>

    <!-- Scheduled Domains Table -->
    <q-card>
      <q-card-section>
        <div class="text-h6">Currently Scheduled Domains</div>
      </q-card-section>
      
      <!-- Filter Controls -->
      <q-card-section>
        <div class="row q-gutter-md">
          <q-input
            v-model="domainFilters.domain"
            outlined
            dense
            placeholder="Filter by domain..."
            style="min-width: 200px"
            clearable
          >
            <template v-slot:prepend>
              <q-icon name="search" />
            </template>
          </q-input>
          
          <q-select
            v-model="domainFilters.country"
            :options="['', ...countryOptions]"
            outlined
            dense
            placeholder="All Countries"
            style="min-width: 150px"
            clearable
            emit-value
            map-options
          />
          
          <q-select
            v-model="domainFilters.prefix"
            :options="['', 'root', 'www', 'aff']"
            outlined
            dense
            placeholder="All Prefixes"
            style="min-width: 120px"
            clearable
          />
          
          <q-select
            v-model="domainFilters.status"
            :options="['', 'Active', 'Late', 'Overdue', 'Never Checked']"
            outlined
            dense
            placeholder="All Status"
            style="min-width: 120px"
            clearable
          />
          
          <q-input
            v-model.number="domainFilters.minInterval"
            outlined
            dense
            type="number"
            placeholder="Min interval"
            style="min-width: 100px"
            clearable
          />
          
          <q-input
            v-model.number="domainFilters.maxInterval"
            outlined
            dense
            type="number"
            placeholder="Max interval"
            style="min-width: 100px"
            clearable
          />
          
          <q-btn
            @click="clearFilters"
            color="grey"
            outline
            icon="clear_all"
            label="Clear Filters"
            size="sm"
          />
        </div>
      </q-card-section>
      
      <q-card-section>
        <q-table
          :rows="filteredScheduledDomains"
          :columns="domainColumns"
          row-key="id"
          :loading="loading"
          :pagination="{ rowsPerPage: 0 }"
          dense
        >
          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <div class="row q-gutter-xs">
                <!-- Manual Check Button - show for Late/Overdue domains or missing from results -->
                <q-btn
                  v-if="shouldShowCheckButton(props.row)"
                  @click="manualCheckDomain(props.row.id)"
                  color="primary"
                  icon="play_arrow"
                  label="CHECK"
                  size="sm"
                  dense
                  :loading="checkingDomains.has(props.row.id)"
                />
                
                <!-- Delete Button -->
                <q-btn
                  @click="deleteScheduledDomain(props.row.id)"
                  color="negative"
                  label="Delete"
                  size="sm"
                  dense
                />
              </div>
            </q-td>
          </template>
          
          <template v-slot:body-cell-last_checked_at="props">
            <q-td :props="props">
              {{ formatDate(props.value) }}
            </q-td>
          </template>
          
          <template v-slot:body-cell-next_check_time="props">
            <q-td :props="props">
              {{ formatDate(props.value) }}
            </q-td>
          </template>
          
          <template v-slot:body-cell-status="props">
            <q-td :props="props">
              <q-chip 
                :color="getStatusColor(props.row)" 
                text-color="white" 
                :icon="getStatusIcon(props.row)"
                size="sm"
                :loading="checkingDomains.has(props.row.id)"
              >
                {{ getStatusText(props.row) }}
              </q-chip>
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>

    <!-- Recent Results -->
    <q-card class="q-mt-lg">
      <q-card-section>
        <div class="text-h6">Recent Monitoring Results</div>
      </q-card-section>
      
      <q-card-section>
        <!-- Filter inputs -->
        <div class="row q-gutter-md q-mb-md">
          <q-input
            v-model="filters.domain"
            label="Filter by Domain"
            outlined
            dense
            clearable
            style="min-width: 200px"
            @update:model-value="filterResults"
          >
            <template v-slot:prepend>
              <q-icon name="search" />
            </template>
          </q-input>
          
          <q-select
            v-model="filters.country"
            :options="countryFilterOptions"
            label="Filter by Country"
            outlined
            dense
            clearable
            emit-value
            map-options
            style="min-width: 150px"
            @update:model-value="filterResults"
          />
          
          <q-input
            v-model="filters.minAvailability"
            label="Min Availability %"
            outlined
            dense
            clearable
            type="number"
            min="0"
            max="100"
            style="min-width: 120px"
            @update:model-value="filterResults"
          />
        </div>
        
        <q-table
          :rows="filteredResults"
          :columns="resultColumns"
          row-key="id"
          :loading="loadingResults"
          :pagination="{ rowsPerPage: 0 }"
          dense
        >
          <template v-slot:body-cell-availability_percentage="props">
            <q-td :props="props">
              <q-badge
                :color="getAvailabilityColor(props.value)"
                :label="props.value + '%'"
              />
            </q-td>
          </template>
          
          <template v-slot:body-cell-checked_at="props">
            <q-td :props="props">
              {{ formatDate(props.value) }}
            </q-td>
          </template>
          
        </q-table>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

export default {
  name: 'ScheduledMonitoring',
  setup() {
    const $q = useQuasar()
    
    // Reactive data
    const loading = ref(false)
    const adding = ref(false)
    const loadingResults = ref(false)
    const scheduledDomains = ref([])
    const recentResults = ref([])
    const filteredResults = ref([])
    const checkingDomains = ref(new Set())
    const timeUpdateInterval = ref(null)
    
    // Filter data
    const filters = ref({
      domain: '',
      country: '',
      minAvailability: ''
    })

    // Domain filter data
    const domainFilters = ref({
      domain: '',
      country: '',
      prefix: '',
      status: '',
      minInterval: null,
      maxInterval: null
    })
    
    const newDomain = ref({
      domain_name: '',
      interval_minutes: 5,
      country: 'China',
      domain_prefix: 'www',
      starting_time: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
    })
    
    // Options for form selects
    const intervalOptions = [
      { label: '1 minute', value: 1 },
      { label: '5 minutes', value: 5 },
      { label: '10 minutes', value: 10 },
      { label: '15 minutes', value: 15 },
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
    
    const prefixOptions = [
      { label: 'root (no prefix)', value: 'root' },
      { label: 'www', value: 'www' },
      { label: 'aff', value: 'aff' }
    ]
    
    // Country filter options (reuse country options)
    const countryFilterOptions = countryOptions
    
    // Helper function to map country codes to display names
    const getCountryDisplayName = (countryCode) => {
      const countryMap = {
        'China': 'China',
        'Vietnam': 'Vietnam', 
        'Indonesia': 'Indonesia',
        'Thailand': 'Thailand',
        'Malaysia': 'Malaysia',
        'Cambodia': 'Cambodia',
        'KR': 'Korea'
      }
      return countryMap[countryCode] || countryCode
    }
    
    // Table columns
    const domainColumns = [
      {
        name: 'domain_name',
        label: 'Domain',
        field: 'domain_name',
        align: 'left',
        sortable: true
      },
      {
        name: 'interval_minutes',
        label: 'Interval (min)',
        field: 'interval_minutes',
        align: 'center',
        sortable: true,
        sort: (a, b) => a - b
      },
      {
        name: 'country',
        label: 'Country',
        field: 'country',
        align: 'center',
        sortable: true,
        format: (val) => getCountryDisplayName(val)
      },
      {
        name: 'domain_prefix',
        label: 'Prefix',
        field: 'domain_prefix',
        align: 'center',
        sortable: true
      },
      {
        name: 'starting_time',
        label: 'Starting Time',
        field: 'starting_time',
        align: 'center',
        sortable: true,
        sort: (a, b) => {
          if (!a) return 1
          if (!b) return -1
          return a.localeCompare(b)
        }
      },
      {
        name: 'last_checked_at',
        label: 'Last Checked',
        field: 'last_checked_at',
        align: 'center',
        sortable: true,
        sort: (a, b) => {
          if (!a) return 1
          if (!b) return -1
          return new Date(b) - new Date(a)
        }
      },
      {
        name: 'next_check_time',
        label: 'Next Check Time',
        field: 'next_check_time',
        align: 'center',
        sortable: true,
        sort: (a, b) => {
          if (!a) return 1
          if (!b) return -1
          return new Date(a) - new Date(b)
        }
      },
      {
        name: 'status',
        label: 'Status',
        field: '',
        align: 'center',
        sortable: true,
        sort: (a, b, rowA, rowB) => {
          const statusPriority = {
            'Active': 1,
            'Late': 2, 
            'Overdue': 3,
            'Never Checked': 4,
            'Checking...': 0
          }
          const statusA = getStatusText(rowA)
          const statusB = getStatusText(rowB)
          return statusPriority[statusA] - statusPriority[statusB]
        }
      },
      {
        name: 'actions',
        label: 'Actions',
        field: '',
        align: 'center'
      }
    ]
    
    const resultColumns = [
      {
        name: 'domain_name',
        label: 'Domain',
        field: 'domain_name',
        align: 'left',
        sortable: true
      },
      {
        name: 'country',
        label: 'Country',
        field: 'country',
        align: 'center',
        sortable: true,
        format: (val) => getCountryDisplayName(val)
      },
      {
        name: 'availability_percentage',
        label: 'Availability',
        field: 'availability_percentage',
        align: 'center',
        sortable: true,
        sort: (a, b) => parseFloat(a) - parseFloat(b)
      },
      {
        name: 'successful_probes',
        label: 'Success/Total',
        field: row => `${row.successful_probes}/${row.total_probes}`,
        align: 'center',
        sortable: true,
        sort: (a, b, rowA, rowB) => {
          const rateA = rowA.successful_probes / rowA.total_probes
          const rateB = rowB.successful_probes / rowB.total_probes
          return rateA - rateB
        }
      },
      {
        name: 'checked_at',
        label: 'Checked At',
        field: 'checked_at',
        align: 'center',
        sortable: true,
        sort: (a, b) => new Date(a) - new Date(b)
      }
    ]
    
    // Methods
    const loadScheduledDomains = async () => {
      try {
        console.log('[SCHEDULED-MONITORING] 🚀 loadScheduledDomains() called')
        loading.value = true
        console.log('[SCHEDULED-MONITORING] 📡 Fetching scheduled domains from API')
        const response = await api.get('/scheduled/api/scheduled-domains')
        
        // Use smart merge to preserve checking state and avoid duplicates
        console.log('[SCHEDULED-MONITORING] 📦 Received', response.data.length, 'domains from API')
        mergeDomainsWithDeduplication(response.data)
        console.log('[SCHEDULED-MONITORING] ✅ Scheduled domains loaded successfully')
        
      } catch (error) {
        console.error('[SCHEDULED-MONITORING] ❌ Error loading scheduled domains:', error)
        console.log('[SCHEDULED-MONITORING] 💥 loadScheduledDomains() failed:', error.message)
        $q.notify({
          type: 'negative',
          message: 'Error loading scheduled domains'
        })
      } finally {
        loading.value = false
      }
    }
    
    const mergeDomainsWithDeduplication = (newDomains) => {
      console.log('[SCHEDULED-MONITORING] 🚀 mergeDomainsWithDeduplication() called with', newDomains.length, 'new domains')
      
      // Create a map of existing domains by ID for efficient lookup
      const existingDomainsMap = new Map()
      scheduledDomains.value.forEach(domain => {
        existingDomainsMap.set(domain.id, domain)
      })
      console.log('[SCHEDULED-MONITORING] 🗺️ Created existing domains map with', existingDomainsMap.size, 'entries')
      
      // Create updated list: preserve existing domains, add new ones, remove deleted ones
      const updatedDomains = []
      const newDomainIds = new Set(newDomains.map(d => d.id))
      console.log('[SCHEDULED-MONITORING] 🆕 New domain IDs received:', Array.from(newDomainIds))
      
      // Add all new/updated domains
      newDomains.forEach(newDomain => {
        // Preserve checking state if domain was already being checked
        if (existingDomainsMap.has(newDomain.id) && checkingDomains.value.has(newDomain.id)) {
          // Keep the checking state when updating existing domain
          console.log('[SCHEDULED-MONITORING] 🔄 Preserving checking state for domain ID:', newDomain.id)
          updatedDomains.push(newDomain)
        } else {
          updatedDomains.push(newDomain)
        }
      })
      console.log('[SCHEDULED-MONITORING] 📋 Merged domains - Updated list has', updatedDomains.length, 'domains')
      
      // Clean up checking state for domains that no longer exist
      const domainsToRemove = []
      checkingDomains.value.forEach(domainId => {
        if (!newDomainIds.has(domainId)) {
          domainsToRemove.push(domainId)
          checkingDomains.value.delete(domainId)
        }
      })
      if (domainsToRemove.length > 0) {
        console.log('[SCHEDULED-MONITORING] 🧹 Cleaned up checking state for removed domains:', domainsToRemove)
      }
      
      // Update the reactive array
      scheduledDomains.value = updatedDomains
      console.log('[SCHEDULED-MONITORING] ✅ Domain merge completed - Final count:', scheduledDomains.value.length)
    }
    
    const loadRecentResults = async () => {
      try {
        console.log('[SCHEDULED-MONITORING] 🚀 loadRecentResults() called')
        loadingResults.value = true
        console.log('[SCHEDULED-MONITORING] 📡 Fetching recent results from API')
        const response = await api.get('/scheduled/api/scheduled-results')
        recentResults.value = response.data
        console.log('[SCHEDULED-MONITORING] 📊 Received', response.data.length, 'recent results')
        filterResults() // Apply current filters to new data
        console.log('[SCHEDULED-MONITORING] ✅ Recent results loaded and filtered successfully')
      } catch (error) {
        console.error('[SCHEDULED-MONITORING] ❌ Error loading recent results:', error)
        console.log('[SCHEDULED-MONITORING] 💥 loadRecentResults() failed:', error.message)
        $q.notify({
          type: 'negative',
          message: 'Error loading recent results'
        })
      } finally {
        loadingResults.value = false
      }
    }
    
    const filterResults = () => {
      console.log('[SCHEDULED-MONITORING] 🚀 filterResults() called')
      let filtered = [...recentResults.value]
      console.log('[SCHEDULED-MONITORING] 🔎 Starting with', filtered.length, 'results')
      
      // Filter by domain name
      if (filters.value.domain && filters.value.domain.trim()) {
        const domainFilter = filters.value.domain.toLowerCase()
        filtered = filtered.filter(result => 
          result.domain_name.toLowerCase().includes(domainFilter)
        )
      }
      
      // Filter by country
      if (filters.value.country) {
        filtered = filtered.filter(result => result.country === filters.value.country)
      }
      
      // Filter by minimum availability percentage
      if (filters.value.minAvailability !== '' && filters.value.minAvailability !== null) {
        const minAvail = parseFloat(filters.value.minAvailability)
        if (!isNaN(minAvail)) {
          filtered = filtered.filter(result => 
            parseFloat(result.availability_percentage) >= minAvail
          )
        }
      }
      
      filteredResults.value = filtered
      console.log('[SCHEDULED-MONITORING] ✅ Filter applied - Final count:', filteredResults.value.length)
    }

    // Computed property for filtered scheduled domains
    const filteredScheduledDomains = computed(() => {
      let filtered = [...scheduledDomains.value]
      
      // Filter by domain name
      if (domainFilters.value.domain && domainFilters.value.domain.trim()) {
        const domainFilter = domainFilters.value.domain.toLowerCase()
        filtered = filtered.filter(domain => 
          domain.domain_name.toLowerCase().includes(domainFilter)
        )
      }
      
      // Filter by country
      if (domainFilters.value.country) {
        filtered = filtered.filter(domain => domain.country === domainFilters.value.country)
      }
      
      // Filter by prefix
      if (domainFilters.value.prefix) {
        filtered = filtered.filter(domain => domain.domain_prefix === domainFilters.value.prefix)
      }
      
      // Filter by status
      if (domainFilters.value.status) {
        filtered = filtered.filter(domain => {
          const status = getStatusText(domain)
          return status === domainFilters.value.status
        })
      }
      
      // Filter by interval range
      if (domainFilters.value.minInterval !== null && domainFilters.value.minInterval !== '') {
        filtered = filtered.filter(domain => domain.interval_minutes >= domainFilters.value.minInterval)
      }
      
      if (domainFilters.value.maxInterval !== null && domainFilters.value.maxInterval !== '') {
        filtered = filtered.filter(domain => domain.interval_minutes <= domainFilters.value.maxInterval)
      }
      
      return filtered
    })
    
    // Clear all domain filters
    const clearFilters = () => {
      domainFilters.value = {
        domain: '',
        country: '',
        prefix: '',
        status: '',
        minInterval: null,
        maxInterval: null
      }
    }
    
    const addScheduledDomain = async () => {
      console.log('[SCHEDULED-MONITORING] 🚀 addScheduledDomain() called')
      console.log('[SCHEDULED-MONITORING] 📝 Domain data:', newDomain.value)
      
      if (!newDomain.value.domain_name) {
        console.log('[SCHEDULED-MONITORING] ❌ Validation failed - no domain name provided')
        $q.notify({
          type: 'negative',
          message: 'Please enter a domain name'
        })
        return
      }
      
      try {
        adding.value = true
        console.log('[SCHEDULED-MONITORING] 📡 Sending domain to API for scheduling')
        const response = await api.post('/scheduled/api/scheduled-domains', newDomain.value)
        console.log('[SCHEDULED-MONITORING] 📦 API response received:', response.data)
        
        // Add the new domain with deduplication instead of simple push
        let addedDomainId = null
        if (response.data.domain) {
          const newDomainData = response.data.domain
          addedDomainId = newDomainData.id
          console.log('[SCHEDULED-MONITORING] 🆕 New domain created with ID:', addedDomainId)
          
          // Use smart merge to avoid duplicates
          mergeDomainsWithDeduplication([newDomainData])
          console.log('[SCHEDULED-MONITORING] 📋 Domain added to local state')
          
          // Add the new domain ID to checking set
          checkingDomains.value.add(addedDomainId)
          console.log('[SCHEDULED-MONITORING] 🔄 Added domain to checking set for initial test')
        } else {
          // Fallback: reload all data if domain data not returned properly
          console.warn('[SCHEDULED-MONITORING] ⚠️ Domain data not found in response, falling back to reload')
          await loadScheduledDomains()
        }
        
        console.log('[SCHEDULED-MONITORING] ✅ Domain scheduling completed successfully')
        $q.notify({
          type: 'positive',
          message: 'Scheduled domain added successfully'
        })
        
        // Keep all form fields unchanged after adding domain
        adding.value = false // Re-enable button immediately
        
        // Remove from checking set after a delay (backend test completes)
        if (addedDomainId) {
          console.log('[SCHEDULED-MONITORING] ⏰ Setting timeout to remove checking state in 10 seconds')
          setTimeout(() => {
            checkingDomains.value.delete(addedDomainId)
            console.log('[SCHEDULED-MONITORING] 🏁 Removed domain', addedDomainId, 'from checking set')
          }, 10000) // 10 seconds for initial check to complete
        }
        
      } catch (error) {
        console.error('[SCHEDULED-MONITORING] ❌ Error adding scheduled domain:', error)
        console.log('[SCHEDULED-MONITORING] 💥 addScheduledDomain() failed:', error.message)
        $q.notify({
          type: 'negative',
          message: 'Error adding scheduled domain'
        })
        adding.value = false // Re-enable button on error too
      }
    }
    
    const deleteScheduledDomain = async (domainId) => {
      try {
        console.log('[SCHEDULED-MONITORING] 🚀 deleteScheduledDomain() called for ID:', domainId)
        console.log('[SCHEDULED-MONITORING] 🗑️ Sending delete request to API')
        await api.delete(`/scheduled/api/scheduled-domains/${domainId}`)
        
        console.log('[SCHEDULED-MONITORING] ✅ Domain deleted successfully from backend')
        $q.notify({
          type: 'positive',
          message: 'Scheduled domain deleted successfully'
        })
        
        // Remove domain immediately from local state for instant UI feedback
        scheduledDomains.value = scheduledDomains.value.filter(domain => domain.id !== domainId)
        console.log('[SCHEDULED-MONITORING] 📋 Removed domain from local state')
        
        // Clean up checking state if domain was being checked
        checkingDomains.value.delete(domainId)
        console.log('[SCHEDULED-MONITORING] 🧹 Cleaned up checking state for deleted domain')
        
      } catch (error) {
        console.error('[SCHEDULED-MONITORING] ❌ Error deleting scheduled domain:', error)
        console.log('[SCHEDULED-MONITORING] 💥 deleteScheduledDomain() failed:', error.message)
        $q.notify({
          type: 'negative',
          message: 'Error deleting scheduled domain'
        })
        
        // Reload data on error to restore correct state
        console.log('[SCHEDULED-MONITORING] 🔄 Reloading data to restore correct state after error')
        loadScheduledDomains()
      }
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return 'Never'
      const date = new Date(dateString)
      return date.toLocaleString('en-US', {
        timeZone: 'Asia/Shanghai',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      })
    }
    
    const getAvailabilityColor = (percentage) => {
      if (percentage >= 80) return 'positive'
      if (percentage >= 60) return 'warning'
      return 'negative'
    }
    
    const getStatusColor = (domain) => {
      if (checkingDomains.value.has(domain.id)) return 'info'
      if (!domain.last_checked_at) return 'grey'
      const now = new Date()
      const lastChecked = new Date(domain.last_checked_at)
      const diffMinutes = (now - lastChecked) / (1000 * 60)
      
      if (diffMinutes > domain.interval_minutes * 2) return 'negative'
      if (diffMinutes > domain.interval_minutes * 1.5) return 'warning'
      return 'positive'
    }
    
    const getStatusIcon = (domain) => {
      if (checkingDomains.value.has(domain.id)) return 'sync'
      if (!domain.last_checked_at) return 'help_outline'
      const now = new Date()
      const lastChecked = new Date(domain.last_checked_at)
      const diffMinutes = (now - lastChecked) / (1000 * 60)
      
      if (diffMinutes > domain.interval_minutes * 2) return 'error'
      if (diffMinutes > domain.interval_minutes * 1.5) return 'warning'
      return 'check_circle'
    }
    
    const getStatusText = (domain) => {
      if (checkingDomains.value.has(domain.id)) return 'Checking...'
      if (!domain.last_checked_at) return 'Never Checked'
      const now = new Date()
      const lastChecked = new Date(domain.last_checked_at)
      const diffMinutes = (now - lastChecked) / (1000 * 60)
      
      if (diffMinutes > domain.interval_minutes * 2) return 'Overdue'
      if (diffMinutes > domain.interval_minutes * 1.5) return 'Late'
      return 'Active'
    }
    
    // Check if domain should have results but doesn't exist in recent results table
    const shouldShowCheckButton = (domain) => {
      // Always show for Late/Overdue domains
      const status = getStatusText(domain)
      if (['Late', 'Overdue'].includes(status)) {
        return true
      }
      
      // Show for domains that should have been checked but missing from recent results
      if (domain.last_checked_at) {
        const now = new Date()
        const lastChecked = new Date(domain.last_checked_at)
        const diffMinutes = (now - lastChecked) / (1000 * 60)
        
        // If it's been at least the interval time, check if domain exists in recent results
        if (diffMinutes >= domain.interval_minutes) {
          // Check if domain exists in recent results for this specific domain+country+prefix combination
          const hasRecentResult = recentResults.value.some(result => 
            result.domain_name === domain.domain_name &&
            result.country === domain.country &&
            result.domain_prefix === domain.domain_prefix
          )
          
          // If no recent result found, show CHECK button
          if (!hasRecentResult) {
            return true
          }
        }
      }
      
      return false
    }
    
    const manualCheckDomain = async (domainId) => {
      try {
        console.log('[SCHEDULED-MONITORING] 🚀 manualCheckDomain() called for ID:', domainId)
        
        // Add domain to checking set to show spinner
        checkingDomains.value.add(domainId)
        console.log('[SCHEDULED-MONITORING] 🔄 Added domain to checking set')
        
        // Call backend API to manually check this domain
        console.log('[SCHEDULED-MONITORING] 📡 Sending manual check request to API')
        const response = await api.post(`/scheduled/api/manual-check/${domainId}`)
        console.log('[SCHEDULED-MONITORING] 📦 Manual check API response:', response.data)
        
        if (response.data.success) {
          console.log('[SCHEDULED-MONITORING] ✅ Manual check initiated successfully')
          $q.notify({
            type: 'positive',
            message: 'Domain check initiated successfully'
          })
          
          // Refresh results after a short delay
          console.log('[SCHEDULED-MONITORING] ⏰ Setting timeout to refresh results in 2 seconds')
          setTimeout(() => {
            console.log('[SCHEDULED-MONITORING] 🔄 Refreshing results after manual check')
            loadRecentResults()
          }, 2000)
        } else {
          console.log('[SCHEDULED-MONITORING] ❌ Manual check failed:', response.data.message)
          throw new Error(response.data.message || 'Manual check failed')
        }
      } catch (error) {
        console.error('[SCHEDULED-MONITORING] ❌ Error during manual check:', error)
        console.log('[SCHEDULED-MONITORING] 💥 manualCheckDomain() failed:', error.message)
        $q.notify({
          type: 'negative',
          message: 'Error initiating manual check'
        })
      } finally {
        // Remove from checking set after 10 seconds
        console.log('[SCHEDULED-MONITORING] ⏰ Setting timeout to remove checking state in 10 seconds')
        setTimeout(() => {
          checkingDomains.value.delete(domainId)
          console.log('[SCHEDULED-MONITORING] 🏁 Removed domain', domainId, 'from checking set after manual check')
        }, 10000)
      }
    }
    
    // Lifecycle
    onMounted(() => {
      console.log('[SCHEDULED-MONITORING] 🚀 Component mounted - starting data loading')
      loadScheduledDomains()
      loadRecentResults()
      
      // Initialize filtered results as empty array
      filteredResults.value = []
      
      // Auto-update starting time every second
      console.log('[SCHEDULED-MONITORING] ⏰ Starting time auto-update interval')
      timeUpdateInterval.value = setInterval(() => {
        newDomain.value.starting_time = new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
      }, 1000)
      
      // Smart auto-refresh every 30 seconds (avoids conflicts during domain additions)
      console.log('[SCHEDULED-MONITORING] 🔄 Starting 30-second auto-refresh interval')
      setInterval(() => {
        // Skip refresh if user is currently adding a domain
        if (!adding.value) {
          console.log('[SCHEDULED-MONITORING] 🔄 Auto-refresh triggered - reloading data')
          loadScheduledDomains()
          loadRecentResults()
        } else {
          console.log('[SCHEDULED-MONITORING] ⏸️ Skipping auto-refresh (user is adding domain)')
        }
      }, 30000)
    })
    
    onBeforeUnmount(() => {
      console.log('[SCHEDULED-MONITORING] 👋 Component unmounting - cleaning up intervals')
      // Clean up time update interval
      if (timeUpdateInterval.value) {
        clearInterval(timeUpdateInterval.value)
        console.log('[SCHEDULED-MONITORING] 🧹 Time update interval cleared')
      }
    })
    
    return {
      loading,
      adding,
      loadingResults,
      scheduledDomains,
      recentResults,
      filteredResults,
      filters,
      domainFilters,
      filteredScheduledDomains,
      countryFilterOptions,
      newDomain,
      intervalOptions,
      countryOptions,
      prefixOptions,
      domainColumns,
      resultColumns,
      checkingDomains,
      addScheduledDomain,
      deleteScheduledDomain,
      manualCheckDomain,
      filterResults,
      clearFilters,
      formatDate,
      getAvailabilityColor,
      getStatusColor,
      getStatusIcon,
      getStatusText,
      shouldShowCheckButton,
      getCountryDisplayName
    }
  }
}
</script>

<style scoped>
.q-page {
  max-width: 1200px;
  margin: 0 auto;
}
</style>