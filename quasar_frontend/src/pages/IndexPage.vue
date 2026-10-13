<template>
<div class="q-pa-md row ">
    <div class="col-2"></div>

    <div class="q-gutter-md col-3">
        <!-- <div >Each domain would need about 3~4mins to query use the red b</div> -->
        <!-- <q-btn @click="e01_force_to_show_the_query_button_and_table()" class="bg-red">force_to_show_the_query_button_and_table</q-btn> -->
        <q-input outlined v-model="intput_example" label="This is an example for the format" disable readonly autogrow />
        <q-input outlined v-model="input_from_jenny_excel" label="Urls for testing" autogrow v-if="show_the_button_and_table === 'show_the_button_and_table'" />
        <q-input outlined v-model="input_from_jenny_excel" label="Urls which is testing" disable readonly autogrow v-if="show_the_button_and_table == 'hide_the_button_and_table'" />
        <q-btn @click="a20_send_to_backend()" v-if="show_the_button_and_table === 'show_the_button_and_table'">send_to_backend</q-btn>

        <div>
            <div class="text-bold"> curl command</div>
            <p class="bg-yellow-3">curl -ILk --tls-max 1.2 -m 10 --http2 {target_ip_for_curl}</p>
        </div>
        <div>
            <div class="text-bold"> example</div>
            <p class="bg-yellow-3"> curl -ILk --tls-max 1.2 -m 10 --http2 https://www.demobrand.example</p>
        </div>
        <div>
            <div class="text-bold"> If either one of the conditions matches, will assume the url is accessible</div>
            <li>curl result must contains cookie name a-demo-cookie</li>
            <li> curl result contains 200</li>
        </div>

    </div>

    <div class="q-pl-md col-6">
        <q-spinner-ios color="yellow" size="3em" v-if="show_the_button_and_table === 'hide_the_button_and_table'" />
        <q-table title="Click Availibility to check detail" class="my-sticky-header-column-table " :rows="list_result_for_table.data" :columns="columns_for_avaiability" v-model:pagination="pagination_for_availability" :filter="filter" row-key="name" virtual-scroll v-if="show_the_button_and_table === 'show_the_button_and_table'" dark color="amber">
            <template v-slot:top-right>
                <q-space />
                <q-input borderless dense debounce="300" color="primary" v-model="filter" class="bg-blue" placeholder="Search">
                    <template v-slot:append>
                        <q-icon name="search" />
                    </template>
                </q-input>
            </template>
            <!-- availibility column -->
            <template v-slot:body-cell-Availiblity="props">
                <q-td>
                    <div class="q-pa-md">
                        <!-- <button_for_availability :dialog="dialog"></button_for_availability> -->
                        <q-btn color="primary" @click="dialog = true , axios_query_raw_data(props.row.which_country,props.row.testing_which_url)">{{props.row.availiblity}}</q-btn>
                        <q-dialog v-model="dialog" persistent :maximized="maximizedToggle" transition-show="slide-up" transition-hide="slide-down">
                            <q-card>
                                <q-bar>
                                    <q-space />
                                    <q-btn dense flat icon="minimize" @click="maximizedToggle = false" :disable="!maximizedToggle">
                                        <q-tooltip v-if="maximizedToggle" class="bg-white text-primary">Minimize</q-tooltip>
                                    </q-btn>
                                    <q-btn dense flat icon="crop_square" @click="maximizedToggle = true" :disable="maximizedToggle">
                                        <q-tooltip v-if="!maximizedToggle" class="bg-white text-primary">Maximize</q-tooltip>
                                    </q-btn>
                                    <q-btn dense flat icon="close" v-close-popup>
                                        <q-tooltip class="bg-white text-primary">Close</q-tooltip>
                                    </q-btn>
                                </q-bar>
                                <q-card-section>
                                    <q-table class="my-sticky-header-column-table " :rows="list_result_for_raw_data" :columns="columns_for_raw_data" row-key="name" virtual-scroll v-model:pagination="pagination_for_raw_data">
                                        <template v-slot:body-cell-link_for_open_cancan_in_browser="props">
                                            <q-td :props="props">
                                                <a target="_blank" :href="props.row.link_for_open_cancan_in_browser">open {{props.row.probe_ip}} in browser</a>
                                            </q-td>
                                        </template>
                                        <template v-slot:body-cell-curl_result_link="props">
                                            <q-td :props="props">
                                                <a target="_blank" :href="props.row.curl_result_link">link</a>
                                            </q-td>
                                        </template>
                                    </q-table>
                                </q-card-section>

                            </q-card>
                        </q-dialog>

                    </div>
                </q-td>
            </template>
        </q-table>
        <child_component_table_for_showing_which_domain_is_being_query_at_the_moment :show_the_button_and_table="show_the_button_and_table" :key="componentKey"></child_component_table_for_showing_which_domain_is_being_query_at_the_moment>
        <!-- componentKey is for re-redering the component -->
        <div v-if="show_the_button_and_table === 'hide_the_button_and_table'"></div>
    </div>

</div>
</template>

<script>
import {
  ref
} from "vue";
import child_component_table_for_showing_which_domain_is_being_query_at_the_moment from "src/components/child_component_table_for_showing_which_domain_is_being_query_at_the_moment.vue"
import axios from "axios";
export default {
  components: {
    child_component_table_for_showing_which_domain_is_being_query_at_the_moment
  },

  setup() {
    // which url is being queried at the moment
    const axios_show_the_button_and_table = ref("http://localhost:5030/a10_lock_the_button_or_table");
    const show_the_button_and_table = ref("show_the_button_and_table")
    const a05_check_if_show_the_query_button_and_table_or_hide_it_when_somebody_is_doing_the_query = async () => {
      // console.log(show_the_button_and_table.value)
      try {
        await axios.get(axios_show_the_button_and_table.value).then((response) => (show_the_button_and_table.value = response.data));

        // when somebody has start querying, if another person opens the browser, then don't query the probe list
        if (show_the_button_and_table.value === "show_the_button_and_table") {
          // console.log(show_the_button_and_table.value)
          a10_get_probe_data()
        }
      } catch (error) {
        throw Error("no data available");
      }
    };
    a05_check_if_show_the_query_button_and_table_or_hide_it_when_somebody_is_doing_the_query()

    // if the button and table is hidden, check every 60sec when to unlock the button and table
    setInterval(() => {
      // console.log(show_the_button_and_table.value)
      if (show_the_button_and_table.value === "hide_the_button_and_table") {
        a05_check_if_show_the_query_button_and_table_or_hide_it_when_somebody_is_doing_the_query();
        axios_query_availibility_db()
        console.log("setInterval if the query has been finished, show the availbility table");
        console.log(Date.now());
      }
    }, 10000);

    // ***************************************

    // const input_from_jenny_excel = ref("https://www.demobrand.example,\nhttps://www.example-games.net,\nhttps://www.example-sports.com,\nhttps://www.example-asia.com,\nhttps://www.example-asia.net,\nhttps://www.demobrand.example,\nhttps://demobrand.example,")
    const input_from_jenny_excel = ref("https://www.demobrand.example,\nhttps://www.example-games.net,")
    const intput_example = ref("https://www.demobrand.example,\nhttps://www.example-games.net,")

    // use frontend to get the probe list 
    const a10_get_probe_data = async () => {
      try {
        let probe_list = await axios.get("http://localhost:5080/axios_show_linux_servers_b11_huck_ge_probes/");
        // post the probe list to backend
        axios.post(
          "http://localhost:5030/a10_init_get_probe_data/", {
          probe_list: probe_list,
        }
        );
      } catch (error) {
        console.error("Failed to get probe data:", error);
        // Continue without probe data - the system can still work with existing data
      }
    };
    const componentKey = ref(0);
    const a20_send_to_backend = async () => {
      show_the_button_and_table.value = "hide_the_button_and_table"
      componentKey.value += 1
      let response = await axios.post(
        "http://localhost:5030/b10_when_received_from_frontend/", {
        input_from_jenny_excel: input_from_jenny_excel.value,
        show_the_button_and_table: show_the_button_and_table.value // send this value to backend, so when 
      }
      );
      // console.log(response.data);
    };

    //************************ for table showing availability //************************

    const pagination_for_availability = ref({
      sortBy: 'desc',
      descending: false,
      rowsPerPage: 5
      // rowsNumber: xx if getting data from a server
    })
    const list_result_for_table = ref([]);
    const columns_for_avaiability = [{
      name: "Availiblity",
      required: true,
      label: "Availiblity",
      align: "left",
      field: (row) => row.availiblity,
      sortable: true,
    },
    {
      name: "Testing_which_url",
      required: true,
      label: "Testing_which_url",
      align: "left",
      field: (row) => row.testing_which_url,
      sortable: true,
    },
    {
      name: "Which_country",
      required: true,
      label: "Which_country",
      align: "left",
      field: (row) => row.which_country,
      sortable: true,
    },
    {
      name: "Wrote_to_db_time",
      required: true,
      label: "Wrote_to_db_time",
      align: "left",
      field: (row) => row.wrote_to_db_time,
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
    axios_query_availibility_db()

    //************************ for table showing raw data in dialog //************************

    const pagination_for_raw_data = ref({
      sortBy: 'desc',
      descending: false,
      rowsPerPage: 1000
    })

    const list_result_for_raw_data = ref([]);
    const axios_query_raw_data = async (check_which_country, check_which_url) => {
      let check_which_url_after_replace = check_which_url.replace("https://", "").replace("http://", "")
      let url_to_get_for_checking_raw_data = `http://localhost:5030/d02_show_raw_data/${check_which_country}/${check_which_url_after_replace}`
      // console.log(`url_to_get_for_checking_raw_data=${url_to_get_for_checking_raw_data}`)
      let response = await axios.get(url_to_get_for_checking_raw_data);
      list_result_for_raw_data.value = response.data;
      console.log(list_result_for_raw_data.value)
    };

    const columns_for_raw_data = [{
      name: "country",
      required: true,
      label: "country",
      align: "left",
      field: (row) => row.country,
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
      name: "isp",
      required: true,
      label: "isp",
      align: "left",
      field: (row) => row.isp,
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
      name: "link_for_open_cancan_in_browser",
      required: true,
      label: "link_for_open_cancan_in_browser",
      align: "left",
      field: (row) => row.link_for_open_cancan_in_browser,
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
    {
      name: "wrote_to_db_time",
      required: true,
      label: "wrote_to_db_time",
      align: "left",
      field: (row) => row.wrote_to_db_time,
      sortable: true,
    },
    {
      name: "country",
      required: true,
      label: "country",
      align: "left",
      field: (row) => row.country,
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

    ];

    //************************ return ************************
    return {
      show_the_button_and_table,
      input_from_jenny_excel,
      a20_send_to_backend,
      list_result_for_table,
      columns_for_avaiability,
      pagination_for_raw_data,
      pagination_for_availability,
      dialog: ref(false),

      axios_query_raw_data,
      columns_for_raw_data,
      list_result_for_raw_data,
      filter: ref(''),
      maximizedToggle: ref(true),
      intput_example,
      componentKey

    };
  },
};
</script>
