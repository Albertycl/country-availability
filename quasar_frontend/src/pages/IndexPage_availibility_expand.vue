<template>
  <div>
    <div class="q-pa-md row">
      <div class="q-gutter-md col-2">
        <q-btn color="red-3" icon="lock" label="unlock" @click="unlock" />
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

        <!-- <q-input outlined v-model="input_is_root_domain" label="Urls which is testing" disable readonly autogrow v-if="show_the_button_and_table == 'hide_the_button_and_table'" /> -->
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
          >{{ isProcessingRequest ? 'PROCESSING...' : 'SEND_TO_BACKEND' }}</q-btn
        >

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
            If either one of the conditions matches, will assume the url is accessible
          </div>
          <div v-if="loadingConditions" class="q-pa-sm">
            <q-spinner color="primary" size="1em" />
            Loading conditions...
          </div>
          <div v-else>
            <!-- Failure Conditions -->
            <div v-for="condition in failureConditions" :key="'fail-' + condition.id">
              <li class="text-red-6">
                {{ condition.condition_pattern }} => cannot connect
                <span v-if="condition.country_specific" class="text-caption"> 
                  ({{ condition.country_specific }})
                </span>
              </li>
            </div>
            <li>---------------------------------------------</li>
            <!-- Success Conditions -->
            <div v-for="condition in successConditions" :key="'success-' + condition.id">
              <li class="text-green-6">
                {{ condition.condition_pattern }} => success
                <span v-if="condition.country_specific" class="text-caption">
                  ({{ condition.country_specific }})
                </span>
              </li>
            </div>
            <li>---------------------------------------------</li>
            <li>others => cannot connect</li>
            
            <!-- Link to Whitelist Management -->
            <div class="q-mt-sm">
              <q-btn 
                size="sm" 
                color="primary" 
                flat 
                icon="settings" 
                label="Manage Conditions" 
                :to="'/whitelist'"
              />
            </div>
          </div>
        </div>
      </div>

      <div class="q-pl-md col-10">
        <div v-if="show_the_button_and_table === 'hide_the_button_and_table'" class="text-center q-pa-md">
          <q-spinner-ios
            color="primary"
            size="4em"
          />
          <div class="text-h6 q-mt-md text-primary">
            <q-icon name="search" size="md" class="q-mr-sm" />
            Checking Availability for {{ urlsBeingCheckedCount }} URLs
          </div>
          <div class="text-caption text-grey-7 q-mt-sm">
            This process takes approximately 4 minutes per domain...
          </div>
          <q-linear-progress
            v-if="progressPercentage > 0"
            :value="progressPercentage / 100"
            color="primary"
            class="q-mt-md"
            rounded
          />
          <div v-if="progressPercentage > 0" class="text-caption q-mt-xs">
            {{ Math.round(progressPercentage) }}% Complete
          </div>
        </div>
        <q-table
          title="Click Availibility to check detail"
          class="my-sticky-header-column-table"
          dense
          :rows="list_result_for_table.data"
          :columns="columns_for_avaiability"
          v-model:pagination="pagination_for_availability"
          :filter="filter"
          row-key="name"
          virtual-scroll
          v-if="show_the_button_and_table === 'show_the_button_and_table'"
          color="primary"
          card-class="bg-orange-2 text-black"
          table-class="text-grey-8"
          table-header-class="text-brown"
          :pagination="initialPagination"
        >
          <template v-slot:top-right>
            <q-space />
            <q-input
              borderless
              dense
              debounce="300"
              color="primary"
              v-model="filter"
              class="bg-blue"
              placeholder="Search"
            >
              <template v-slot:append>
                <q-icon name="search" />
              </template>
            </q-input>
          </template>
          <!-- availibility column -->
          <template v-slot:body-cell-Availiblity="props">
            <q-td>
              <div class="q-pa-md">
                <child_component_availibility_button
                  :key="`${props.row.which_country}+${props.row.testing_which_url}`"
                  :some_country="props.row.which_country"
                  :some_url="props.row.testing_which_url"
                  :availiblity="props.row.availiblity"
                  @toggle-expansion="handleRowExpansion"
                ></child_component_availibility_button>
              </div>
            </q-td>
          </template>
        </q-table>

        <!-- Expanded details section outside the table -->
        <div v-if="expandedRow" class="q-mt-md q-pa-md bg-grey-2">
          <div class="text-h6 q-mb-md">
            Details for {{ expandedRow.country }} - {{ expandedRow.url }}
            <q-btn flat round icon="close" @click="closeExpansion" class="float-right" />
          </div>
          <q-table 
            :rows="expandedRowData" 
            :columns="columns_for_raw_data" 
            row-key="name" 
            v-model:pagination="pagination_for_raw_data" 
            virtual-scroll 
            card-class="grey-8 text-black" 
            table-class="text-grey-8" 
            table-header-class="text-brown" 
            dense
          >
            <template v-slot:body-cell-open_probe_in_browser="props">
              <q-td :props="props">
                <a target="_blank" :href="props.row.link_for_open_cancan_in_browser">open {{props.row.probe_ip}} in browser</a>
              </q-td>
            </template>
            <template v-slot:body-cell-can_access_or_not="props">
              <q-td :props="props" style="word-wrap: break-word; word-break: break-word; white-space: normal; max-width: 300px;">
                <div class="bg-red-3" v-if="props.row.can_access_or_not.includes('cannot')" style="word-wrap: break-word; white-space: normal;">{{props.row.can_access_or_not}}</div>
                <div v-if="!props.row.can_access_or_not.includes('cannot') && !props.row.can_access_or_not.includes('52770')" style="word-wrap: break-word; white-space: normal;">{{props.row.can_access_or_not}}</div>
                <div class="bg-orange-3" v-if="props.row.can_access_or_not.includes('Unable to connect to port 52770')" style="word-wrap: break-word; white-space: normal;">{{props.row.can_access_or_not}}</div>
                <!-- Show matched condition for any detected condition -->
                <div v-if="props.row.matched_condition"
                     class="q-mt-xs q-pa-xs rounded-borders text-weight-bold"
                     style="word-wrap: break-word; white-space: normal;"
                     :class="props.row.matched_condition === 'demo-redirect-3' || props.row.matched_condition === 'xiao301' ? 'bg-orange-2 text-orange-8' : 'bg-blue-2 text-blue-8'">
                  🎯 Condition Hit: {{ props.row.matched_condition }}
                </div>
              </q-td>
            </template>
            <template v-slot:body-cell-can_access_internet_or_not="props">
              <q-td :props="props" style="word-wrap: break-word; word-break: break-word; white-space: normal; max-width: 250px;">
                <div class="bg-green-3" v-if="props.row.can_access_internet_or_not.includes('can_access_internet')" style="word-wrap: break-word; white-space: normal;">{{props.row.can_access_internet_or_not}}</div>
                <div v-if="!props.row.can_access_internet_or_not.includes('can_access_internet')" style="word-wrap: break-word; white-space: normal;">{{props.row.can_access_internet_or_not}}</div>
              </q-td>
            </template>
            <template v-slot:body-cell-curl_result_link="props">
              <q-td :props="props" style="word-wrap: break-word; word-break: break-word; white-space: normal; max-width: 200px;">
                <div style="word-wrap: break-word; white-space: normal;">
                  <child_component_open_link :link="props.row.curl_result_link"></child_component_open_link>
                </div>
                <!-- Highlight condition match for any detected condition -->
                <div v-if="props.row.matched_condition"
                     class="q-mt-xs q-pa-xs rounded-borders text-weight-bold"
                     style="word-wrap: break-word; white-space: normal;"
                     :class="props.row.matched_condition === 'demo-redirect-3' || props.row.matched_condition === 'xiao301' ? 'bg-yellow-2 text-orange-8' : 'bg-green-2 text-green-8'">
                  ⚡ {{ props.row.matched_condition }} found in curl result
                </div>
              </q-td>
            </template>
          </q-table>
        </div>

        <child_component_table_for_showing_which_domain_is_being_query_at_the_moment
          :show_the_button_and_table="show_the_button_and_table"
          :key="componentKey"
          v-if="show_the_button_and_table === 'hide_the_button_and_table'"
        ></child_component_table_for_showing_which_domain_is_being_query_at_the_moment>
        <!-- componentKey is for re-rendering the component -->
        <div v-if="show_the_button_and_table === 'hide_the_button_and_table'"></div>
        <q-btn
          color="primary"
          label="copy_to_clipboard"
          @click="copyGroupedData()"
          class="q-mt-md text-h4"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, watchEffect, computed } from "vue";
import child_component_availibility_button from "src/components/child_component_availibility_button.vue";
import child_component_table_for_showing_which_domain_is_being_query_at_the_moment from "src/components/child_component_table_for_showing_which_domain_is_being_query_at_the_moment.vue";
import child_component_open_link from "src/components/child_component_open_link.vue";
import axios from "axios";
import { copyToClipboard, Notify } from "quasar";
export default {
  components: {
    child_component_table_for_showing_which_domain_is_being_query_at_the_moment,
    child_component_availibility_button,
    child_component_open_link,
  },

  setup() {
    // use frontend to get the probe list

    const copyGroupedData = () => {
  const data = list_result_for_table.value.data;

  // Function to extract base URL for grouping
  const getBaseURL = (url) => {
    return url.replace(/^(https?:\/\/)?(www\.|aff\.)?/, '');
  };

  // Function to categorize URL type
  const getUrlType = (url) => {
    if (url.includes('www.')) return 'www';
    if (url.includes('aff.')) return 'aff';
    return 'root';
  };

  // Sort data by base URL, country, and then URL type
  data.sort((a, b) => {
    const baseComparison = getBaseURL(a.testing_which_url).localeCompare(getBaseURL(b.testing_which_url));
    if (baseComparison !== 0) return baseComparison;
    const countryComparison = a.which_country.localeCompare(b.which_country);
    if (countryComparison !== 0) return countryComparison;
    return getUrlType(a.testing_which_url).localeCompare(getUrlType(b.testing_which_url));
  });

  let formattedData = '';
  let lastBaseURL = '';
  let lastCountry = '';

  data.forEach((item, index) => {
    const country = item.which_country;
    const url = item.testing_which_url;
    const availability = parseFloat(item.availiblity).toFixed(2) + "%";
    const baseURL = getBaseURL(url);
    const urlType = getUrlType(url);

    // Check for new base URL
    if (baseURL !== lastBaseURL) {
      if (lastBaseURL) formattedData += '\n';  // Add a space before starting a new base URL group
      formattedData += baseURL + '\n';
      lastCountry = '';  // Reset country for new base URL group
    }

    // Check for new country under the same base URL
    if (country !== lastCountry) {
      if (lastCountry) formattedData += '\n';  // Add a newline to separate different countries
      formattedData += country + '\n';
    }

    formattedData += `${urlType} ${availability}\n`;
    lastBaseURL = baseURL;
    lastCountry = country;
  });

  copyToClipboard(formattedData)
    .then(() => {
      console.log('Data copied to clipboard!');
      // Optional: notify the user of success
    })
    .catch(() => {
      console.error('Failed to copy data');
      // Optional: notify the user of failure
    });
};

    const unlock = async () => {
      let probe_list = await axios.get("http://localhost:5030/unlock_itself");
    };

    const a10_get_probe_data = async () => {
      // post the probe list to backend
      axios.post("http://localhost:5030/a10_init_get_probe_data/", {
        probe_list: probe_list,
      });
    };
    a10_get_probe_data();

    // which url is being queried at the moment
    const axios_show_the_button_and_table = ref(
      "http://localhost:5030/a10_lock_the_button_or_table"
    );
    const show_the_button_and_table = ref("show_the_button_and_table");
    const a05_check_if_show_the_query_button_and_table_or_hide_it_when_somebody_is_doing_the_query = async () => {
      // console.log(show_the_button_and_table.value)
      try {
        await axios
          .get(axios_show_the_button_and_table.value)
          .then((response) => (show_the_button_and_table.value = response.data));

        // when somebody has start querying, if another person opens the browser, then don't query the probe list
        // if (show_the_button_and_table.value === "show_the_button_and_table") {
        //   a10_get_probe_data()
        // }
      } catch (error) {
        throw Error("no data available");
      }
    };
    a05_check_if_show_the_query_button_and_table_or_hide_it_when_somebody_is_doing_the_query();

    // if the button and table is hidden, check every 60sec when to unlock the button and table
    setInterval(() => {
      // console.log(show_the_button_and_table.value)
      if (show_the_button_and_table.value === "hide_the_button_and_table") {
        a05_check_if_show_the_query_button_and_table_or_hide_it_when_somebody_is_doing_the_query();
        if (componentKey.value < 2) {
          componentKey.value += 1;
        }
        axios_query_availibility_db();
        console.log(
          "setInterval if the query has been finished, show the availbility table"
        );
        // console.log(Date.now());
      }
    }, 10000);

    // ***************************************

    // const input_is_root_domain = ref("https://www.demobrand.example,\nhttps://www.example-games.net,\nhttps://www.example-sports.com,\nhttps://www.example-asia.com,\nhttps://www.example-asia.net,\nhttps://www.demobrand.example,\nhttps://demobrand.example,")
    const input_is_root_domain = ref("demobrand.example,\nexample-games.net,");
    // const converted_root_to_www_m_aff = ref("https://demobrand.example,\nhttps://example-games.net,")
    const converted_root_to_www_m_aff = ref("");

    const a10_check_which_domains_were_queried_last_time = async () => {
      let url_to_query = `http://localhost:5030/b10_which_url_has_been_queried_from_last_request`;
      let response = await axios.get(url_to_query);
      input_is_root_domain.value = response.data;
    };
    a10_check_which_domains_were_queried_last_time();
    // ***************************************

    const componentKey = ref(0);
    
    // Validation logic for send button
    const isValidSelectionForSending = computed(() => {
      const hasCountrySelected = list_testing_avalibility_in_which_country.value.length > 0;
      const hasPrefixSelected = list_root_www_m_aff.value.length > 0;
      return hasCountrySelected && hasPrefixSelected;
    });
    
    const handleSendToBackend = () => {
      if (!isValidSelectionForSending.value) {
        const missingSelections = [];
        if (list_testing_avalibility_in_which_country.value.length === 0) {
          missingSelections.push("country");
        }
        if (list_root_www_m_aff.value.length === 0) {
          missingSelections.push("prefix (root/www/aff)");
        }

        Notify.create({
          type: 'warning',
          message: `Please select at least one ${missingSelections.join(' and one ')} before sending to backend`,
          position: 'top',
          timeout: 3000,
          actions: [{ icon: 'close', color: 'white' }]
        });
        return;
      }

      // Show processing state
      isProcessingRequest.value = true;

      Notify.create({
        type: 'positive',
        message: `Starting availability check for ${urlsToBeChecked.value.length} URLs across ${list_testing_avalibility_in_which_country.value.length} countries`,
        position: 'top',
        timeout: 5000,
        actions: [{ icon: 'close', color: 'white' }]
      });

      a20_send_to_backend();
    };
    
    const a20_send_to_backend = async () => {
      componentKey.value = 0;
      show_the_button_and_table.value = "hide_the_button_and_table";
      componentKey.value += 1;
      let response = await axios.post(
        "http://localhost:5030/b10_when_received_from_frontend/",
        {
          input_from_jenny_excel: after_converting_to_the_domain_iwanta_query.value,
          show_the_button_and_table: show_the_button_and_table.value,
          list_testing_avalibility_in_which_country:
            list_testing_avalibility_in_which_country.value,
        }
      );

      // Reset processing state when transitioning to monitoring phase
      isProcessingRequest.value = false;
    };

    //************************ for table showing availability //************************

    const pagination_for_availability = ref({
      sortBy: "desc",
      descending: false,
      rowsPerPage: 5,
      // rowsNumber: xx if getting data from a server
    });
    const list_result_for_table = ref([]);
    const columns_for_avaiability = [
      {
        name: "Which_country",
        requiChina: true,
        label: "Which_country",
        align: "left",
        field: (row) => row.which_country,
        sortable: true,
      },

      {
        name: "Testing_which_url",
        requiChina: true,
        label: "Testing_which_url",
        align: "left",
        field: (row) => row.testing_which_url,
        sortable: true,
      },
      {
        name: "Availiblity",
        requiChina: true,
        label: "Availiblity",
        align: "left",
        field: (row) => row.availiblity,
        sortable: true,
      },
    ];

    const url = ref("http://localhost:5030/d01_show_availibility_table/");

    const axios_query_availibility_db = async () => {
      try {
        await axios.get(url.value).then((data) => (list_result_for_table.value = data));
      } catch (error) {
        throw Error("no data available");
      }
    };
    axios_query_availibility_db();

    //************************ for table showing raw data in dialog //************************

    const pagination_for_raw_data = ref({
      sortBy: "desc",
      descending: false,
      rowsPerPage: 100,
    });

    const columns_for_raw_data = [
      {
        name: "country",
        required: true,
        label: "Country",
        align: "left",
        field: (row) => row.country,
        sortable: true,
      },
      {
        name: "isp",
        required: true,
        label: "ISP",
        align: "left",
        field: (row) => row.isp,
        sortable: true,
      },
      {
        name: "url_that_im_testing",
        required: true,
        label: "url_that_im_testing",
        align: "left",
        field: (row) => row.url_that_im_testing,
        sortable: true,
      },
      {
        name: "probe_ip",
        required: true,
        label: "probe_ip",
        align: "left",
        field: (row) => row.probe_ip,
        sortable: true,
      },
      {
        name: "can_access_internet_or_not",
        required: true,
        label: "can_access_internet_or_not",
        align: "left",
        field: (row) => row.can_access_internet_or_not,
        sortable: true,
      },
      {
        name: "open_probe_in_browser",
        required: true,
        label: "open_probe_in_browser",
        align: "left",
        field: (row) => row.link_for_open_cancan_in_browser,
        sortable: true,
      },
      {
        name: "can_access_or_not",
        required: true,
        label: "can_access_or_not",
        align: "left",
        field: (row) => row.can_access_or_not,
        sortable: true,
      },
      {
        name: "curl_result_link",
        required: true,
        label: "curl_result_link",
        align: "left",
        field: (row) => row.curl_result_link,
        sortable: true,
      },
    ];

    // pick which country you want to test
    const list_testing_avalibility_in_which_country = ref([]);
    const list_root_www_m_aff = ref([]);
    const after_converting_to_the_domain_iwanta_query = ref("");
    watchEffect(() => {
      after_converting_to_the_domain_iwanta_query.value = "";
      // Split by any whitespace (newlines, spaces, tabs) or commas
      let list_after_split_input_is_root_domain = input_is_root_domain.value
        .split(/[\s,]+/)
        .map(item => item.trim())
        .filter(item => item !== '' && item.includes('.'));
      console.log('=== NEW CODE LOADED ===');
      console.log('Split count:', list_after_split_input_is_root_domain.length);
      console.log('Split result:', list_after_split_input_is_root_domain);
      if (list_after_split_input_is_root_domain.slice(-1) == ",") {
        console.log();
      }
      list_after_split_input_is_root_domain.forEach((each_root_domain) => {
        list_root_www_m_aff.value.forEach((each_root_www_m_aff) => {
          if (each_root_domain != "") {
            console.log(`each_root_domain=${each_root_domain}`);
            // console.log(`each_root_domain=${each_root_domain} / each_root_www_m_aff=${each_root_www_m_aff}`)
            // console.log(`each_root_domain=${each_root_domain}`)
            if (each_root_www_m_aff == "root") {
              after_converting_to_the_domain_iwanta_query.value = `https://${each_root_domain},\n${after_converting_to_the_domain_iwanta_query.value}`;
              // console.log(`after_converting_to_the_domain_iwanta_query=${after_converting_to_the_domain_iwanta_query.value}`)
              // https://demobrand.example,\nhttps://example-games.net,
            } else if (each_root_www_m_aff == "www") {
              after_converting_to_the_domain_iwanta_query.value = `https://www.${each_root_domain},\n${after_converting_to_the_domain_iwanta_query.value}`;
            } else if (each_root_www_m_aff == "aff") {
              after_converting_to_the_domain_iwanta_query.value = `https://aff.${each_root_domain},\n${after_converting_to_the_domain_iwanta_query.value}`;
            } else if (each_root_www_m_aff == "m") {
              after_converting_to_the_domain_iwanta_query.value = `https://m.${each_root_domain},\n${after_converting_to_the_domain_iwanta_query.value}`;
            }
          }
        });
      });
    });

    //************************ Interactive Features ************************
    const isProcessingRequest = ref(false);

    // Computed property for URLs to be checked
    const urlsToBeChecked = computed(() => {
      if (!after_converting_to_the_domain_iwanta_query.value) return [];
      return after_converting_to_the_domain_iwanta_query.value
        .split(',')
        .map(url => url.trim())
        .filter(url => url && url !== '');
    });

    // Computed property for URLs being checked count
    const urlsBeingCheckedCount = computed(() => {
      return urlsToBeChecked.value.length * list_testing_avalibility_in_which_country.value.length;
    });

    // Function to get countries for a specific URL
    const getCountriesForUrl = (url) => {
      return list_testing_avalibility_in_which_country.value;
    };

    // Computed property for progress percentage (you can enhance this with actual progress data)
    const progressPercentage = computed(() => {
      // This is a simple example. You can enhance this to calculate actual progress
      // based on data from the child component or backend API
      if (show_the_button_and_table.value === 'hide_the_button_and_table') {
        // You can implement actual progress tracking here
        return 0; // Will be updated by actual progress data
      }
      return 0;
    });

    //************************ Whitelist Conditions ************************
    const whitelistConditions = ref([])
    const loadingConditions = ref(false)
    
    const successConditions = computed(() => 
      whitelistConditions.value.filter(c => c.condition_type === 'success' && c.is_enabled)
    )
    
    const failureConditions = computed(() => 
      whitelistConditions.value.filter(c => c.condition_type === 'failure' && c.is_enabled)
    )
    
    const fetchWhitelistConditions = async () => {
      try {
        loadingConditions.value = true
        console.log('[MAIN PAGE] 📥 Fetching enabled whitelist conditions...')
        
        const response = await axios.get('http://localhost:5030/whitelist/api/whitelist/conditions/enabled')
        whitelistConditions.value = response.data
        
        console.log(`[MAIN PAGE] ✅ Loaded ${whitelistConditions.value.length} enabled conditions`)
      } catch (error) {
        console.error('[MAIN PAGE] ❌ Error fetching whitelist conditions:', error)
        // Fallback to default hardcoded conditions if API fails
        whitelistConditions.value = []
      } finally {
        loadingConditions.value = false
      }
    }
    
    // Load conditions on component mount
    fetchWhitelistConditions()

    //************************ Row Expansion Handling ************************
    const expandedRow = ref(null)
    const expandedRowData = ref([])
    
    const handleRowExpansion = async (rowInfo) => {
      if (rowInfo.isExpanded) {
        // If expanding this row, close any other expanded row and load data
        expandedRow.value = {
          country: rowInfo.country,
          url: rowInfo.url,
          componentId: rowInfo.componentId
        }
        // Load the detailed data for this row
        await loadExpandedRowData(rowInfo.country, rowInfo.url)
      } else {
        // If collapsing, close the expansion
        expandedRow.value = null
        expandedRowData.value = []
      }
    }
    
    const loadExpandedRowData = async (country, url) => {
      try {
        let check_which_url_after_replace = url.replace("https://", "").replace("http://", "")
        let url_to_get_for_checking_raw_data = `http://localhost:5030/d02_show_raw_data/${country}/${check_which_url_after_replace}`
        let response = await axios.get(url_to_get_for_checking_raw_data)
        expandedRowData.value = response.data
      } catch (error) {
        console.error('Error loading expanded row data:', error)
        expandedRowData.value = []
      }
    }
    
    const closeExpansion = () => {
      expandedRow.value = null
      expandedRowData.value = []
    }

    //************************ return ************************
    return {
      show_the_button_and_table,
      input_is_root_domain,
      a20_send_to_backend,
      list_result_for_table,
      columns_for_avaiability,
      pagination_for_raw_data,
      pagination_for_availability,

      columns_for_raw_data,
      filter: ref(""),
      maximizedToggle: ref(true),
      converted_root_to_www_m_aff,
      componentKey,
      list_testing_avalibility_in_which_country,
      list_root_www_m_aff,
      after_converting_to_the_domain_iwanta_query,
      unlock,
      copyGroupedData,
      initialPagination: {
        sortBy: "desc",
        descending: false,
        page: 1,
        rowsPerPage: 100,
        // rowsNumber: xx if getting data from a server
      },

      // Validation for send button
      isValidSelectionForSending,
      handleSendToBackend,

      // Interactive features
      isProcessingRequest,
      urlsToBeChecked,
      urlsBeingCheckedCount,
      getCountriesForUrl,
      progressPercentage,

      // Whitelist conditions
      whitelistConditions,
      loadingConditions,
      successConditions,
      failureConditions,
      fetchWhitelistConditions,

      // Row expansion
      expandedRow,
      expandedRowData,
      handleRowExpansion,
      closeExpansion
    };
  },
};
</script>
