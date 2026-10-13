<template>
  <div>
    <div class="q-pa-md row">
      <div class="q-gutter-md col-2" style="max-height: 100vh; overflow-y: auto;">
        <q-input
          outlined
          v-model="input_is_root_domain"
          label="Enter Root Domain ex:demobrand.example, dont enter https"
          autogrow
          v-if="show_the_button_and_table === 'show_the_button_and_table'"
        />
        <div>
          <div class="bg-deep-purple-1 q-mt-md">
            <div class="q-gutter-sm">
              <q-checkbox
                v-model="list_testing_avalibility_in_which_country"
                val="Brazil"
                label="Brazil"
              />
              <q-checkbox
                v-model="list_testing_avalibility_in_which_country"
                val="Cambodia"
                label="Cambodia"
              />
              <q-checkbox
                v-model="list_testing_avalibility_in_which_country"
                val="China"
                label="China"
              />
            </div>
            <div class="q-gutter-sm">
              <q-checkbox
                v-model="list_testing_avalibility_in_which_country"
                val="Indonesia"
                label="Indonesia"
              />
              <q-checkbox
                v-model="list_testing_avalibility_in_which_country"
                val="KR"
                label="KR"
              />
              <q-checkbox
                v-model="list_testing_avalibility_in_which_country"
                val="Malaysia"
                label="Malaysia"
              />
            </div>

            <div class="q-gutter-sm">
              <q-checkbox
                v-model="list_testing_avalibility_in_which_country"
                val="Thailand"
                label="Thailand"
              />
              <q-checkbox
                v-model="list_testing_avalibility_in_which_country"
                val="Vietnam"
                label="Vietnam"
              />
            </div>
          </div>
          <div class="bg-light-green-1 q-mt-md">
            <q-checkbox v-model="list_root_www_m_aff" val="root" label="root" />
            <q-checkbox v-model="list_root_www_m_aff" val="www" label="www" />
            <q-checkbox v-model="list_root_www_m_aff" val="aff" label="aff" />
          </div>
        </div>

        <q-input
          outlined
          v-model="after_converting_to_the_domain_iwanta_query"
          label="Will curl these domains"
          disable
          readonly
          autogrow
        />

        <!-- Display URLs being checked -->
        <div v-if="show_the_button_and_table === 'show_the_button_and_table' && urlsToBeChecked.length > 0" class="q-mt-md">
          <div class="text-subtitle2 text-primary q-mb-sm">
            <q-icon name="list" class="q-mr-xs" />
            URLs to be checked ({{ urlsToBeChecked.length }} total):
          </div>
          <q-list bordered separator class="rounded-borders bg-grey-1" style="max-height: 200px; overflow-y: auto;">
            <q-item v-for="(url, index) in urlsToBeChecked" :key="index" dense>
              <q-item-section>
                <q-item-label class="text-body2">{{ url }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-chip size="sm" color="grey-4" text-color="grey-8">
                  {{ getCountriesForUrl(url).join(', ') }}
                </q-chip>
              </q-item-section>
            </q-item>
          </q-list>
        </div>

        <q-btn
          @click="handleSendToBackend()"
          v-if="show_the_button_and_table === 'show_the_button_and_table'"
          :color="isValidSelectionForSending ? 'primary' : 'warning'"
          :loading="isProcessingRequest"
          :disable="isProcessingRequest"
          icon-right="send"
        >{{ isProcessingRequest ? 'PROCESSING...' : 'SEND_TO_BACKEND' }}
        </q-btn>

        <div>
          <div class="text-bold">curl command</div>
          <p class="bg-yellow-3">
            curl -L --insecure {target_ip_for_curl} -A'Mozilla/5.0 (Windows NT 10.0;
            Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0
            Safari/537.36'
          </p>
        </div>
        <div>
          <div class="text-bold">example</div>
          <p class="bg-yellow-3">
            curl -L --insecure https://www.demobrand.example -A'Mozilla/5.0 (Windows NT 10.0;
            Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0
            Safari/537.36'
          </p>
        </div>
        <div>
          <div class="text-bold">
            🔍 FILTERED LOGIC: Success conditions checked FIRST
          </div>
          <div v-if="loadingConditions" class="q-pa-sm">
            <q-spinner color="primary" size="1em" />
            Loading conditions...
          </div>
          <div v-else>
            <div class="q-mt-md q-mb-sm">
              <q-btn
                size="md"
                color="primary"
                icon="settings"
                label="Manage Conditions"
                :to="'/whitelist'"
                class="full-width"
              />
            </div>

            <q-expansion-item
              icon="error"
              label="Failure Conditions"
              default-closed
              header-class="text-red-6"
            >
              <div style="max-height: 150px; overflow-y: auto;">
                <div v-for="condition in failureConditions" :key="'fail-' + condition.id">
                  <li class="text-red-6 text-caption">
                    {{ condition.condition_pattern }} => cannot connect
                    <span v-if="condition.country_specific" class="text-caption">
                      ({{ condition.country_specific }})
                    </span>
                  </li>
                </div>
              </div>
            </q-expansion-item>

            <q-expansion-item
              icon="check_circle"
              label="Success Conditions"
              default-closed
              header-class="text-green-6"
              class="q-mt-sm"
            >
              <div style="max-height: 400px; overflow-y: auto;">
                <div v-for="condition in successConditions" :key="'success-' + condition.id">
                  <li class="text-green-6 text-caption">
                    {{ condition.condition_pattern }} => success
                    <span v-if="condition.country_specific" class="text-caption">
                      ({{ condition.country_specific }})
                    </span>
                  </li>
                </div>
              </div>
            </q-expansion-item>
          </div>
        </div>
      </div>

      <div class="q-pl-md col-10">
        <div v-if="show_the_button_and_table === 'hide_the_button_and_table'" class="text-center q-pa-md">
          <!-- Enhanced loading animation with rotating icons -->
          <div class="row justify-center items-center q-gutter-md">
            <q-spinner-ios
              color="primary"
              size="4em"
            />
            <div class="column">
              <div class="text-h6 text-primary">
                <q-icon name="search" size="md" class="q-mr-sm" />
                🔍 Processing {{ urlsBeingCheckedCount }} URLs with FILTERED Logic
              </div>
              <div class="text-subtitle2 text-orange-8 q-mt-xs" v-if="currentProcessingStep">
                <q-icon name="settings" class="rotating q-mr-sm" />
                {{ currentProcessingStep }}
              </div>
            </div>
          </div>

          <!-- Processing steps timeline -->
          <div class="q-mt-md" v-if="processingSteps.length > 0">
            <div class="text-caption text-grey-7 q-mb-sm text-center">
              Success conditions checked FIRST, then failure conditions, unknown results excluded from availability calculation
            </div>
            <q-timeline color="primary" layout="comfortable" class="q-mt-md">
              <q-timeline-entry
                v-for="(step, index) in processingSteps"
                :key="index"
                :title="step.title"
                :subtitle="step.subtitle"
                :icon="step.icon"
                :color="step.completed ? 'positive' : step.active ? 'primary' : 'grey-5'"
              >
                <div v-if="step.active" class="text-caption">
                  <q-linear-progress
                    :value="step.progress / 100"
                    :color="step.completed ? 'positive' : 'primary'"
                    size="8px"
                    rounded
                    class="q-mt-xs"
                  />
                  <div class="q-mt-xs">{{ Math.round(step.progress) }}% Complete</div>
                </div>
              </q-timeline-entry>
            </q-timeline>
          </div>

          <!-- Overall progress -->
          <div class="q-mt-md">
            <q-linear-progress
              v-if="progressPercentage > 0"
              :value="progressPercentage / 100"
              color="primary"
              size="12px"
              rounded
              class="q-mt-md"
            />
            <div v-if="progressPercentage > 0" class="text-center text-caption q-mt-xs text-primary">
              <strong>Overall Progress: {{ Math.round(progressPercentage) }}%</strong>
            </div>
          </div>

          <!-- Backend Log Display -->
          <div class="q-mt-md" v-if="backendLogs.length > 0">
            <div class="text-subtitle2 text-grey-7 q-mb-xs">
              <q-icon name="terminal" class="q-mr-xs" /> Backend Logs
            </div>
            <div
              ref="logContainer"
              class="bg-grey-9 text-green-4 q-pa-sm rounded-borders"
              style="max-height: 400px; overflow-y: auto; font-family: monospace; font-size: 11px; line-height: 1.4;"
            >
              <div v-for="(log, index) in backendLogs" :key="index">
                {{ log.message }}
              </div>
            </div>
          </div>
        </div>
        <q-table
          title="🔍 Click Availability to check detail (FILTERED LOGIC)"
          flat
          bordered
          :rows="list_result_for_table.data"
          :columns="columns_for_avaiability"
          v-model:pagination="pagination_for_availability"
          :filter="filter"
          row-key="name"
          v-if="show_the_button_and_table === 'show_the_button_and_table'"
          color="primary"
          table-style="table-layout: fixed; width: 100%"
        >
          <template v-slot:top-right>
            <q-btn
              flat
              dense
              icon="content_copy"
              label="Copy"
              color="primary"
              class="q-mr-md"
              @click="copyFormattedResults"
            />
            <q-input
              borderless
              dense
              debounce="300"
              color="primary"
              v-model="filter"
              placeholder="Search"
              class="bg-grey-2"
            >
              <template v-slot:append>
                <q-icon name="search" />
              </template>
            </q-input>
          </template>


          <!-- Enhanced Availability column with unknown results -->
          <template v-slot:body-cell-Availiblity="props">
            <q-td :props="props" class="text-center">
              <q-btn
                :color="(props.row.unknown_count > 0) ? 'orange' : 'primary'"
                @click="handleRowExpansion(props.row)"
              >
                {{ props.row.availiblity }}%
              </q-btn>
              <div class="text-caption q-mt-xs">
                <span class="text-positive">✅{{ props.row.success_count || 0 }}</span> |
                <span class="text-negative">❌{{ props.row.failure_count || 0 }}</span> |
                <span class="text-orange">❓{{ props.row.unknown_count || 0 }}</span>
              </div>
              <div class="text-caption text-grey-7">(click to check each probe detail status)</div>
            </q-td>
          </template>
        </q-table>

        <!-- Expanded details section outside the table -->
        <div v-for="expandedRow in expandedRows" :key="expandedRow.componentId" class="q-mt-md">
          <q-card flat bordered>
            <q-card-section>
              <div class="text-h6">
                🔍 Detailed Results for {{ expandedRow.url }} in {{ expandedRow.country }}
                <q-btn flat dense round icon="close" @click="closeExpansion(expandedRow.componentId)" class="float-right"/>
              </div>

              <!-- Enhanced summary cards for unknown results -->
              <div class="row q-gutter-sm q-mb-md">
                <q-card flat class="bg-positive text-white col">
                  <q-card-section class="text-center">
                    <div class="text-h4">{{ expandedRow.summary_stats.success_count }}</div>
                    <div>✅ Success</div>
                  </q-card-section>
                </q-card>
                <q-card flat class="bg-negative text-white col">
                  <q-card-section class="text-center">
                    <div class="text-h4">{{ expandedRow.summary_stats.failure_count }}</div>
                    <div>❌ Failure</div>
                  </q-card-section>
                </q-card>
                <q-card flat class="bg-orange text-white col">
                  <q-card-section class="text-center">
                    <div class="text-h4">{{ expandedRow.summary_stats.unknown_count }}</div>
                    <div>❓ Unknown</div>
                  </q-card-section>
                </q-card>
              </div>

              <!-- Raw data table with enhanced unknown result access -->
              <q-table
                title="Raw Probe Results (FILTERED LOGIC)"
                :rows="expandedRow.rawData"
                :columns="columns_for_raw_data"
                dense
                class="my-sticky-header-table"
                virtual-scroll
                style="max-height: 400px"
                table-style="table-layout: fixed; width: 100%;"
                :pagination="{ rowsPerPage: 0 }"
              >
                <!-- Internet access indicator column -->
                <template v-slot:body-cell-can_access_internet_or_not="props">
                  <q-td :props="props" class="text-center">
                    <q-chip
                      v-if="props.value && props.value.includes('can_access_internet')"
                      color="green"
                      text-color="white"
                      size="sm"
                      icon="wifi">
                      Yes
                    </q-chip>
                    <q-chip
                      v-else-if="props.value && props.value !== 'None' && props.value.trim() !== ''"
                      color="red"
                      text-color="white"
                      size="sm"
                      icon="wifi_off">
                      No
                    </q-chip>
                    <q-chip
                      v-else
                      color="grey"
                      text-color="white"
                      size="sm"
                      icon="help">
                      N/A
                    </q-chip>
                  </q-td>
                </template>

                <!-- Status indicator column -->
                <template v-slot:body-cell-can_access_or_not="props">
                  <q-td :props="props">
                    <q-chip
                      :color="getStatusColor(props.value)"
                      text-color="white"
                      size="sm"
                      :icon="getStatusIcon(props.value)">
                      {{ props.value || 'Unknown' }}
                    </q-chip>
                  </q-td>
                </template>

                <!-- Enhanced curl result link column -->
                <template v-slot:body-cell-curl_result_link="props">
                  <q-td :props="props" class="text-center">
                    <q-btn
                      size="sm"
                      color="info"
                      @click="openCurlResult(props.value)"
                      v-if="props.value && props.value !== 'skip'"
                      icon="open_in_new">
                      View Result
                    </q-btn>
                    <span v-else class="text-grey">No result</span>
                  </q-td>
                </template>

                <!-- Matched condition column -->
                <template v-slot:body-cell-matched_condition="props">
                  <q-td :props="props" class="text-center">
                    <q-chip
                      v-if="props.value"
                      size="sm"
                      :color="isFailureCondition(props.value) ? 'red' : 'green'"
                      text-color="white"
                      :icon="isFailureCondition(props.value) ? 'cancel' : 'check_circle'">
                      {{ props.value }}
                    </q-chip>
                    <span v-else class="text-grey">No match</span>
                  </q-td>
                </template>
              </q-table>
            </q-card-section>
          </q-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from "vue";
import axios from "axios";
import { useQuasar } from "quasar";

export default {
  setup() {
    const $q = useQuasar();

    // State management matching original page
    const show_the_button_and_table = ref("show_the_button_and_table");
    const input_is_root_domain = ref("");
    const list_testing_avalibility_in_which_country = ref([]);
    const list_root_www_m_aff = ref([]);
    const after_converting_to_the_domain_iwanta_query = ref("");
    const list_result_for_table = ref({ data: [] });
    const filter = ref("");
    const isProcessingRequest = ref(false);
    const urlsBeingCheckedCount = ref(0);
    const progressPercentage = ref(0);
    const currentProcessingStep = ref("");
    const processingSteps = ref([]);

    // Enhanced state for filtered functionality
    const expandedRows = ref([]);
    const loadingConditions = ref(true);
    const successConditions = ref([]);
    const failureConditions = ref([]);

    // Log streaming state
    const sessionId = ref(null);
    const backendLogs = ref([]);
    const lastLogId = ref(0);
    const logPollingInterval = ref(null);

    // Computed properties matching original
    const urlsToBeChecked = computed(() => {
      if (!input_is_root_domain.value || list_testing_avalibility_in_which_country.value.length === 0 || list_root_www_m_aff.value.length === 0) {
        return [];
      }

      // Split by any whitespace (newlines, spaces, tabs) or commas
      const domains = input_is_root_domain.value
        .split(/[\s,]+/)
        .map(item => item.trim())
        .filter(item => item !== '' && item.includes('.'));

      const urls = [];

      // Generate URLs for each domain with selected prefixes
      for (const domain of domains) {
        for (const prefix of list_root_www_m_aff.value) {
          if (prefix === 'root') {
            urls.push(`https://${domain}`);
          } else {
            urls.push(`https://${prefix}.${domain}`);
          }
        }
      }
      return urls;
    });

    const isValidSelectionForSending = computed(() => {
      return input_is_root_domain.value.trim() &&
             list_testing_avalibility_in_which_country.value.length > 0 &&
             list_root_www_m_aff.value.length > 0;
    });

    // Check if a matched condition is a failure condition
    const isFailureCondition = (conditionValue) => {
      if (!conditionValue) return false;
      return failureConditions.value.some(fc =>
        fc.condition_pattern && conditionValue.toLowerCase().includes(fc.condition_pattern.toLowerCase())
      );
    };

    // Watch for URL generation
    watch([input_is_root_domain, list_testing_avalibility_in_which_country, list_root_www_m_aff], () => {
      after_converting_to_the_domain_iwanta_query.value = urlsToBeChecked.value.join(', ');
    }, { immediate: true });

    // Table columns with proper widths
    const columns_for_avaiability = [
      {
        name: "testing_which_url",
        required: true,
        label: "Testing URL",
        align: "left",
        field: (row) => row.testing_which_url,
        sortable: true,
        style: "width: 35%;",
        headerStyle: "width: 35%"
      },
      {
        name: "which_country",
        required: true,
        label: "Country",
        align: "left",
        field: (row) => row.which_country,
        sortable: true,
        style: "width: 15%;",
        headerStyle: "width: 15%"
      },
      {
        name: "Availiblity",
        required: true,
        label: "Availability",
        align: "center",
        field: (row) => row.availiblity,
        sortable: true,
        style: "width: 25%;",
        headerStyle: "width: 25%"
      },
      {
        name: "Wrote_to_db_time",
        required: true,
        label: "Updated",
        align: "left",
        field: (row) => row.wrote_to_db_time,
        sortable: true,
        style: "width: 25%;",
        headerStyle: "width: 25%"
      },
    ];

    const columns_for_raw_data = [
      {
        name: "country",
        required: true,
        label: "Country",
        align: "left",
        field: (row) => row.country,
        sortable: true,
        style: "width: 70px;",
        headerStyle: "width: 70px;",
      },
      {
        name: "url_that_im_testing",
        required: true,
        label: "URL",
        align: "left",
        field: (row) => row.url_that_im_testing ? row.url_that_im_testing.replace(/^FILTERED_/, '') : '',
        sortable: true,
        style: "width: 180px; max-width: 180px; word-wrap: break-word; white-space: normal;",
        headerStyle: "width: 180px;",
      },
      {
        name: "isp",
        required: true,
        label: "ISP",
        align: "left",
        field: (row) => row.isp,
        sortable: true,
        style: "width: 80px;",
        headerStyle: "width: 80px;",
      },
      {
        name: "probe_ip",
        required: true,
        label: "Probe IP",
        align: "left",
        field: (row) => row.probe_ip,
        sortable: true,
        style: "width: 120px;",
        headerStyle: "width: 120px;",
      },
      {
        name: "can_access_internet_or_not",
        required: true,
        label: "Internet",
        align: "center",
        field: (row) => row.can_access_internet_or_not,
        sortable: true,
        style: "width: 80px;",
        headerStyle: "width: 80px;",
      },
      {
        name: "can_access_or_not",
        required: true,
        label: "Status",
        align: "left",
        field: (row) => row.can_access_or_not,
        sortable: true,
        style: "width: 220px;",
        headerStyle: "width: 220px;",
      },
      {
        name: "curl_result_link",
        required: true,
        label: "Curl Result",
        align: "center",
        field: (row) => row.curl_result_link,
        sortable: true,
        style: "width: 120px;",
        headerStyle: "width: 120px;",
      },
      {
        name: "matched_condition",
        required: true,
        label: "Matched",
        align: "center",
        field: (row) => row.matched_condition,
        sortable: true,
        style: "width: 120px;",
        headerStyle: "width: 120px;",
      },
      {
        name: "wrote_to_db_time",
        required: true,
        label: "Time",
        align: "left",
        field: (row) => row.wrote_to_db_time,
        sortable: true,
        style: "width: 150px;",
        headerStyle: "width: 150px;",
      }
    ];

    const pagination_for_availability = ref({
      sortBy: 'desc',
      descending: false,
      rowsPerPage: 1000
    });

    // API Functions
    const loadWhitelistConditions = async () => {
      try {
        loadingConditions.value = true;
        const response = await axios.get("http://localhost:5030/whitelist/api/whitelist/conditions/enabled");
        const conditions = response.data;

        // Sort success conditions with demobrand/DEMOBRAND at the bottom
        const successList = conditions.filter(c => c.condition_type === 'success');
        successConditions.value = successList.sort((a, b) => {
          const aIs188 = a.condition_pattern && (a.condition_pattern.toLowerCase() === 'demobrand');
          const bIs188 = b.condition_pattern && (b.condition_pattern.toLowerCase() === 'demobrand');
          if (aIs188 && !bIs188) return 1;
          if (!aIs188 && bIs188) return -1;
          return 0;
        });
        failureConditions.value = conditions.filter(c => c.condition_type === 'failure');
      } catch (error) {
        console.error("Error loading conditions:", error);
        // Fallback to show some basic conditions
        successConditions.value = [{ condition_pattern: "a-demo-cookie", id: 1 }];
        failureConditions.value = [{ condition_pattern: "timeout", id: 2 }];
      } finally {
        loadingConditions.value = false;
      }
    };

    const axios_query_availibility_db = async () => {
      try {
        const response = await axios.get("http://localhost:5030/api/filtered/results");
        // Transform the data to match original format but with enhanced counts
        const transformedData = response.data.map(item => {
          // Clean up concatenated URLs from backend
          let cleanUrl = item.url;
          if (cleanUrl && (cleanUrl.includes('https://') || cleanUrl.includes('http://'))) {
            const urlMatches = cleanUrl.match(/(https?:\/\/[^\s<>"{}|\\^`\[\]]+)/g);
            if (urlMatches && urlMatches.length > 0) {
              cleanUrl = urlMatches[0]; // Use the first valid URL found
            }
          }

          return {
            ...item,
            testing_which_url: cleanUrl,
            which_country: item.country,
            availiblity: item.availability,
            wrote_to_db_time: item.updated_at,
            success_count: item.success_count,
            failure_count: item.failure_count,
            unknown_count: item.unknown_count
          };
        });

        list_result_for_table.value = { data: transformedData };

        // Auto-expand all rows after data loads
        setTimeout(() => {
          transformedData.forEach(row => {
            handleRowExpansion(row);
          });
        }, 500);
      } catch (error) {
        console.error("Error fetching availability data:", error);
        list_result_for_table.value = { data: [] };
      }
    };

    // Fetch results filtered by current test parameters (domain + countries)
    const axios_query_availibility_db_filtered = async () => {
      try {
        const response = await axios.get("http://localhost:5030/api/filtered/results");

        // Get current test parameters - split by whitespace or commas
        const currentDomains = input_is_root_domain.value
          .split(/[\s,]+/)
          .map(item => item.trim().toLowerCase())
          .filter(item => item !== '' && item.includes('.'));
        const currentCountries = list_testing_avalibility_in_which_country.value;
        const currentPrefixes = list_root_www_m_aff.value;

        // Build list of URLs we're testing
        const urlsBeingTested = [];
        for (const domain of currentDomains) {
          for (const prefix of currentPrefixes) {
            if (prefix === 'root') {
              urlsBeingTested.push(`https://${domain}`);
            } else {
              urlsBeingTested.push(`https://${prefix}.${domain}`);
            }
          }
        }

        // Transform and filter the data
        const transformedData = response.data
          .map(item => {
            let cleanUrl = item.url;
            if (cleanUrl && (cleanUrl.includes('https://') || cleanUrl.includes('http://'))) {
              const urlMatches = cleanUrl.match(/(https?:\/\/[^\s<>"{}|\\^`\[\]]+)/g);
              if (urlMatches && urlMatches.length > 0) {
                cleanUrl = urlMatches[0];
              }
            }

            return {
              ...item,
              testing_which_url: cleanUrl,
              which_country: item.country,
              availiblity: item.availability,
              wrote_to_db_time: item.updated_at,
              success_count: item.success_count,
              failure_count: item.failure_count,
              unknown_count: item.unknown_count
            };
          })
          .filter(item => {
            // Filter by country
            const countryMatch = currentCountries.includes(item.which_country);

            // Filter by URL - check if the URL exactly matches one of the URLs being tested
            const itemUrl = item.testing_which_url ? item.testing_which_url.toLowerCase().trim() : '';
            const urlMatch = urlsBeingTested.some(testUrl =>
              itemUrl === testUrl.toLowerCase()
            );

            return countryMatch && urlMatch;
          });

        list_result_for_table.value = { data: transformedData };
      } catch (error) {
        console.error("Error fetching filtered availability data:", error);
        list_result_for_table.value = { data: [] };
      }
    };

    // Helper function to simulate processing steps
    const simulateStep = async (stepIndex, description) => {
      processingSteps.value[stepIndex].active = true;
      processingSteps.value[stepIndex].subtitle = description;

      // Animate progress for this step
      for (let i = 0; i <= 100; i += 20) {
        processingSteps.value[stepIndex].progress = i;
        progressPercentage.value = ((stepIndex * 100) + i) / processingSteps.value.length;
        await new Promise(resolve => setTimeout(resolve, 400));
      }

      processingSteps.value[stepIndex].completed = true;
      processingSteps.value[stepIndex].active = false;
    };

    // Start polling for backend logs
    const startLogPolling = () => {
      if (logPollingInterval.value) return;
      logPollingInterval.value = setInterval(async () => {
        if (!sessionId.value) return;
        try {
          const response = await axios.get(`http://localhost:5030/api/logs/${sessionId.value}?last_id=${lastLogId.value}`);
          const newLogs = response.data;
          if (newLogs.length > 0) {
            backendLogs.value.push(...newLogs);
            lastLogId.value = newLogs[newLogs.length - 1].id;
            // Update current step based on logs
            updateStepFromLogs(newLogs);
          }
        } catch (error) {
          console.error("Error polling logs:", error);
        }
      }, 2000);
    };

    // Stop log polling and clean up
    const stopLogPolling = async () => {
      if (logPollingInterval.value) {
        clearInterval(logPollingInterval.value);
        logPollingInterval.value = null;
      }
      // Clean up logs from database
      if (sessionId.value) {
        try {
          await axios.delete(`http://localhost:5030/api/logs/${sessionId.value}`);
        } catch (error) {
          console.error("Error cleaning up logs:", error);
        }
      }
    };

    // Update stepper based on backend logs
    const updateStepFromLogs = (newLogs) => {
      for (const log of newLogs) {
        const msg = log.message;
        // Update current processing step display
        if (msg.includes('[STEP')) {
          currentProcessingStep.value = msg;
        }
        // Parse step number and update stepper
        const stepMatch = msg.match(/\[STEP (\d)\/5\]/);
        if (stepMatch) {
          const stepNum = parseInt(stepMatch[1]) - 1;
          // Mark all previous steps as completed
          for (let i = 0; i < stepNum; i++) {
            if (processingSteps.value[i]) {
              processingSteps.value[i].completed = true;
              processingSteps.value[i].active = false;
              processingSteps.value[i].progress = 100;
            }
          }
          // Set current step as active
          if (processingSteps.value[stepNum]) {
            processingSteps.value[stepNum].active = true;
            processingSteps.value[stepNum].progress = 50;
          }
          // Update overall progress
          progressPercentage.value = (stepNum / 5) * 100;
        }
        // Check for completion
        if (msg.includes('COMPLETED')) {
          for (let i = 0; i < processingSteps.value.length; i++) {
            processingSteps.value[i].completed = true;
            processingSteps.value[i].active = false;
            processingSteps.value[i].progress = 100;
          }
          progressPercentage.value = 100;
        }
      }
    };

    const handleSendToBackend = async () => {
      if (!isValidSelectionForSending.value) {
        alert("Please select domain, countries, and prefixes");
        return;
      }

      // Clear previous test results before starting new test
      list_result_for_table.value = { data: [] };
      expandedRows.value = [];
      backendLogs.value = [];
      lastLogId.value = 0;

      // Generate unique session ID
      sessionId.value = `session_${Date.now()}`;

      isProcessingRequest.value = true;
      show_the_button_and_table.value = "hide_the_button_and_table";
      urlsBeingCheckedCount.value = urlsToBeChecked.value.length;
      progressPercentage.value = 0;

      // Initialize processing steps
      processingSteps.value = [
        { title: "Preparing URLs", subtitle: "Generating test URLs for probes", icon: "dns", active: true, completed: false, progress: 0 },
        { title: "Distributing to Probes", subtitle: "Sending curl commands to global probe servers", icon: "cloud_upload", active: false, completed: false, progress: 0 },
        { title: "Executing Curl Commands", subtitle: "Running availability tests from multiple locations", icon: "terminal", active: false, completed: false, progress: 0 },
        { title: "Analyzing Results", subtitle: "Applying FILTERED logic: success conditions first", icon: "analytics", active: false, completed: false, progress: 0 },
        { title: "Calculating Availability", subtitle: "Computing final availability percentages", icon: "calculate", active: false, completed: false, progress: 0 }
      ];

      // Start polling for logs
      startLogPolling();

      try {
        currentProcessingStep.value = "Sending URLs to backend for processing...";
        const data_for_backend = {
          input_from_jenny_excel: after_converting_to_the_domain_iwanta_query.value,
          list_testing_avalibility_in_which_country: list_testing_avalibility_in_which_country.value,
          session_id: sessionId.value
        };

        await axios.post("http://localhost:5030/filtered/process_urls", data_for_backend, {
          headers: { 'Content-Type': 'application/json' }
        });

        // Complete all steps
        progressPercentage.value = 100;
        currentProcessingStep.value = "✅ Processing complete! Loading results...";

        setTimeout(async () => {
          // Stop polling and clean up
          await stopLogPolling();
          // Fetch results filtered by current test parameters
          axios_query_availibility_db_filtered();
          show_the_button_and_table.value = "show_the_button_and_table";
          isProcessingRequest.value = false;
          progressPercentage.value = 0;
          currentProcessingStep.value = "";
          processingSteps.value = [];
        }, 1500);

      } catch (error) {
        console.error("Error processing URLs:", error);
        await stopLogPolling();
        show_the_button_and_table.value = "show_the_button_and_table";
        isProcessingRequest.value = false;
        currentProcessingStep.value = "";
        processingSteps.value = [];
        alert("Error processing URLs. Please try again.");
      }
    };

    // Enhanced row expansion handling
    const handleRowExpansion = async (row) => {
      const componentId = `${row.which_country}_${row.testing_which_url.replace(/[^a-zA-Z0-9]/g, '_')}`;

      // Check if already expanded
      const existingIndex = expandedRows.value.findIndex(r => r.componentId === componentId);
      if (existingIndex >= 0) {
        expandedRows.value.splice(existingIndex, 1);
        return;
      }

      // Load raw data for this row - For filtered page, data is stored with FILTERED_ prefix
      try {
        let rawData = [];

        // Since this is the filtered page, URLs in database are stored as:
        // "FILTERED_https://www.example.com" but API endpoint adds "https://" prefix
        // So we need to construct the URL properly for the API
        const originalUrl = row.testing_which_url;  // e.g. "https://www.example-random.net"

        // Fix for concatenated URLs - extract only the first valid URL
        let cleanUrl = originalUrl;
        if (originalUrl.includes('https://') || originalUrl.includes('http://')) {
          // Extract the first valid URL from potentially concatenated string
          const urlMatches = originalUrl.match(/(https?:\/\/[^\s<>"{}|\\^`\[\]]+)/g);
          if (urlMatches && urlMatches.length > 0) {
            cleanUrl = urlMatches[0]; // Use the first valid URL found
          }
        }

        const urlWithoutProtocol = cleanUrl.replace("https://", "").replace("http://", "");  // e.g. "www.example-random.net"
        const filteredUrlForAPI = `FILTERED_${urlWithoutProtocol}`;  // e.g. "FILTERED_www.example-random.net"

        // URL encode the filteredUrlForAPI to handle any special characters
        const encodedFilteredUrl = encodeURIComponent(filteredUrlForAPI);

        let url_to_get_for_checking_raw_data = `http://localhost:5030/d02_show_raw_data_filtered/${row.which_country}/${encodedFilteredUrl}`;

        console.log(`[FILTERED_DEBUG] Original URL: ${originalUrl}`);
        console.log(`[FILTERED_DEBUG] Cleaned URL: ${cleanUrl}`);
        console.log(`[FILTERED_DEBUG] URL for API: ${filteredUrlForAPI}`);
        console.log(`[FILTERED_DEBUG] Expected DB URL: https://${filteredUrlForAPI}`);
        console.log(`[FILTERED_DEBUG] API URL: ${url_to_get_for_checking_raw_data}`);

        let response = await axios.get(url_to_get_for_checking_raw_data);
        rawData = response.data;

        // Use backend-provided counts (same as summary row) instead of recalculating
        expandedRows.value.push({
          componentId,
          country: row.which_country,
          url: row.testing_which_url,
          rawData,
          summary_stats: {
            success_count: row.success_count || 0,
            failure_count: row.failure_count || 0,
            unknown_count: row.unknown_count || 0
          }
        });

        console.log(`[FILTERED_EXPANSION] Loaded ${rawData.length} probe results: ${row.success_count} success, ${row.failure_count} failure, ${row.unknown_count} unknown`);
      } catch (error) {
        console.error("Error loading raw data:", error);
        // Add empty row with error indication
        expandedRows.value.push({
          componentId,
          country: row.which_country,
          url: row.testing_which_url,
          rawData: [],
          summary_stats: { success_count: 0, failure_count: 0, unknown_count: 0 }
        });
      }
    };

    const closeExpansion = (componentId) => {
      const index = expandedRows.value.findIndex(r => r.componentId === componentId);
      if (index >= 0) {
        expandedRows.value.splice(index, 1);
      }
    };

    const getCountriesForUrl = (url) => {
      return list_testing_avalibility_in_which_country.value;
    };

    // Helper functions for status display
    const getStatusColor = (status) => {
      if (!status) return "grey";
      if (status.includes("can access")) return "positive";
      if (status.includes("cannot access")) return "negative";
      return "orange";
    };

    const getStatusIcon = (status) => {
      if (!status) return "help";
      if (status.includes("can access")) return "check_circle";
      if (status.includes("cannot access")) return "cancel";
      return "help_outline";
    };

    const openCurlResult = async (url) => {
      if (url && url !== "skip") {
        try {
          // Use backend proxy to fetch curl result content (avoids CORS issues)
          const proxyUrl = `http://localhost:5030/proxy_curl_result?url=${encodeURIComponent(url)}`;
          const response = await axios.get(proxyUrl);
          const curlContent = response.data;

          // Check if content is empty or whitespace only
          if (!curlContent || curlContent.trim().length === 0) {
            $q.dialog({
              title: 'Curl Result',
              message: `<div style="padding: 20px; text-align: center; color: #666;">
                <div style="font-size: 48px; margin-bottom: 15px;">📭</div>
                <div style="font-size: 16px; margin-bottom: 10px;"><strong>Empty Curl Result</strong></div>
                <div style="font-size: 14px; line-height: 1.5;">
                  This probe returned no content. Possible reasons:<br>
                  • Network timeout or connection failed<br>
                  • Target website returned empty response<br>
                  • DNS resolution failed<br>
                  • Target server refused connection
                </div>
              </div>`,
              html: true,
              fullWidth: true,
              fullHeight: false
            });
            return;
          }

          // Escape HTML in content to prevent XSS
          const escapedContent = curlContent
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');

          // Show curl content in a dialog
          $q.dialog({
            title: 'Curl Result',
            message: `<pre style="white-space: pre-wrap; word-wrap: break-word; font-family: monospace; background-color: #f5f5f5; padding: 15px; border-radius: 4px; max-height: 500px; overflow-y: auto; font-size: 12px;">${escapedContent}</pre>`,
            html: true,
            fullWidth: true,
            fullHeight: false
          });
        } catch (error) {
          console.error('Error fetching curl result:', error);
          $q.notify({
            type: 'negative',
            message: 'Failed to load curl result'
          });
        }
      }
    };

    // Copy formatted results to clipboard
    const copyFormattedResults = () => {
      const data = list_result_for_table.value.data || [];
      if (data.length === 0) {
        $q.notify({ type: 'warning', message: 'No results to copy' });
        return;
      }

      // Group results by base domain and country
      const grouped = {};
      data.forEach(item => {
        // Extract base domain and prefix from URL like "https://aff.demobrand.example"
        let url = item.testing_which_url || '';
        url = url.replace(/^https?:\/\//, ''); // Remove protocol

        let prefix = 'root';
        let baseDomain = url;

        // Check for common prefixes
        const prefixMatch = url.match(/^(www|aff|m)\./i);
        if (prefixMatch) {
          prefix = prefixMatch[1].toLowerCase();
          baseDomain = url.replace(/^(www|aff|m)\./i, '');
        }

        const country = item.which_country || 'Unknown';
        const key = `${baseDomain}__${country}`;

        if (!grouped[key]) {
          grouped[key] = { domain: baseDomain, country: country, prefixes: {} };
        }
        grouped[key].prefixes[prefix] = item.availiblity;
      });

      // Format output
      const lines = [];
      Object.values(grouped).forEach(group => {
        lines.push(group.domain);
        lines.push(group.country);
        // Output prefixes in order: aff, root, www
        ['aff', 'root', 'www'].forEach(prefix => {
          if (group.prefixes[prefix] !== undefined) {
            // Format availability with 2 decimal places
            const availability = parseFloat(group.prefixes[prefix]).toFixed(2);
            lines.push(`${prefix} ${availability}%`);
          }
        });
        lines.push(''); // Empty line between domains
      });

      const text = lines.join('\n').trim();

      // Use fallback method for HTTP (non-secure context)
      const copyToClipboard = (str) => {
        // Try modern clipboard API first (requires HTTPS)
        if (navigator.clipboard && window.isSecureContext) {
          return navigator.clipboard.writeText(str);
        }
        // Fallback for HTTP using textarea
        const textarea = document.createElement('textarea');
        textarea.value = str;
        textarea.style.position = 'fixed';
        textarea.style.left = '-9999px';
        document.body.appendChild(textarea);
        textarea.select();
        try {
          document.execCommand('copy');
          document.body.removeChild(textarea);
          return Promise.resolve();
        } catch (err) {
          document.body.removeChild(textarea);
          return Promise.reject(err);
        }
      };

      copyToClipboard(text).then(() => {
        $q.notify({ type: 'positive', message: 'Results copied to clipboard' });
      }).catch(() => {
        $q.notify({ type: 'negative', message: 'Failed to copy to clipboard' });
      });
    };

    // Initialize data
    onMounted(() => {
      loadWhitelistConditions();
      axios_query_availibility_db();
    });

    return {
      // State
      show_the_button_and_table,
      input_is_root_domain,
      list_testing_avalibility_in_which_country,
      list_root_www_m_aff,
      after_converting_to_the_domain_iwanta_query,
      list_result_for_table,
      filter,
      isProcessingRequest,
      urlsBeingCheckedCount,
      progressPercentage,
      currentProcessingStep,
      processingSteps,
      expandedRows,
      loadingConditions,
      successConditions,
      failureConditions,
      backendLogs,

      // Computed
      urlsToBeChecked,
      isValidSelectionForSending,

      // Helper functions
      isFailureCondition,

      // Table definitions
      columns_for_avaiability,
      columns_for_raw_data,
      pagination_for_availability,

      // Methods
      handleSendToBackend,
      handleRowExpansion,
      closeExpansion,
      getCountriesForUrl,
      getStatusColor,
      getStatusIcon,
      openCurlResult,
      copyFormattedResults,
    };
  }
};
</script>

<style scoped>
.rotating {
  animation: rotation 2s infinite linear;
}

@keyframes rotation {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(359deg);
  }
}
</style>

<style lang="sass">
.my-sticky-header-column-table
  thead tr:first-child th
    background-color: #c1f0fc

.my-sticky-header-column-table td:first-child
  background-color: #f5f5f5

.my-sticky-header-column-table thead tr:last-child th
  position: sticky
  top: 48px
  z-index: 2

.my-sticky-header-column-table thead tr:first-child th:first-child
  z-index: 3

.my-sticky-header-column-table td:first-child
  position: sticky
  left: 0
  z-index: 1

.my-sticky-header-table
  thead tr th
    position: sticky
    z-index: 1
    background-color: #1976d2
    color: white

  thead tr:first-child th
    top: 0

.q-table--dark
  .my-sticky-header-column-table thead tr:first-child th
    background-color: #1976d2

  .my-sticky-header-column-table td:first-child
    background-color: #424242
</style>