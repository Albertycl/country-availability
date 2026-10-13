<template>
<div class="q-pa-md row">
    <button_for_availability></button_for_availability>
    <div class="q-gutter-md col" style="max-width: 300px">
        <q-input outlined v-model="input_from_jenny_excel" label="Outlined" autogrow />
        <q-btn @click="a20_send_to_backend()">send_to_backend</q-btn>
    </div>

    <div class="q-pl-md col">
        
    <q-table
      style="height: 100%"
      title="Availability"
      class="my-sticky-header-column-table "
      :rows="list_result_for_table.data"
      :columns="columns_for_avaiability"
      v-model:pagination="pagination_for_availability"
      :filter="filter"
      row-key="name"
      virtual-scroll
    >
      <template v-slot:top>
        <q-space />
        <q-input borderless dense debounce="300" color="primary" v-model="filter" class="bg-blue" placeholder="Search">
          <template v-slot:append>
            <q-icon name="search" />
          </template>
        </q-input>
      </template>
      <template v-slot:body-cell-availiblity="props">
        <q-td>
          <div class="q-pa-md">
            dialog={{dialog}}
            <q-btn  color="primary" @click="dialog = true , axios_query_raw_data(props.row.which_country,props.row.testing_which_url)" >{{props.row.availiblity}}</q-btn>
            <q-dialog v-model="dialog">
              <q-card>
                <q-card-section>
                  <q-table
                    style="height: 100%"
                    title="Raw Data"
                    class="my-sticky-header-column-table "
                    :rows="list_result_for_raw_data"
                    :columns="columns_for_raw_data"
                    row-key="name"
                    virtual-scroll
                    v-model:pagination="pagination_for_raw_data"
                  >
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
  </div>

</div>
</template>

<script>
import { ref } from "vue";
import axios from "axios";
export default {
  components: {
  },
  setup() {
    const input_from_jenny_excel = ref("https://www.demobrand.example,\nhttps://www.example-games.net,\nhttps://www.example-sports.com,\nhttps://www.example-asia.com,\nhttps://www.example-asia.net,\nhttps://www.demobrand.example,\nhttps://demobrand.example,")
    // const input_from_jenny_excel = ref("https://www.demobrand.example,\nhttps://www.example-games.net,")

    // use frontend to get the probe list 
    const a10_get_probe_data = async () => {
      let probe_list = await axios.get(
        "http://localhost:5040/axios_show_which_host_isp_for_webpaping/all",
      );
      // post the probe list to backend
      axios.post(
        "http://localhost:5030/a10_init_get_probe_data/", {
        probe_list: probe_list,
      }
      );
    };
    a10_get_probe_data()
    const a20_send_to_backend = async () => {
      let response = await axios.post(
        "http://localhost:5030/b10_when_received_from_frontend/", {
        input_from_jenny_excel: input_from_jenny_excel.value,
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
    const columns_for_avaiability = [
      {
        name: "availiblity",
        required: true,
        label: "availiblity",
        align: "left",
        field: (row) => row.availiblity,
        sortable: true,
      },
      {
        name: "testing_which_url",
        required: true,
        label: "testing_which_url",
        align: "left",
        field: (row) => row.testing_which_url,
        sortable: true,
      },
      {
        name: "which_country",
        required: true,
        label: "which_country",
        align: "left",
        field: (row) => row.which_country,
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


    ];

    const url = ref("http://localhost:5030/d01_show_availibility_table/"
    );

    const axios_query_availibility_db = async () => {
      try {
        await axios.get(url.value).then((data) => (list_result_for_table.value = data));
        console.log(list_result_for_table.value.data)
      } catch (error) {
        throw Error("no data available");
      }
    };
    axios_query_availibility_db()


    //************************ for table showing raw data in dialog //************************

    const pagination_for_raw_data = ref({
      sortBy: 'desc',
      descending: false,
      rowsPerPage: 100
    })

    const list_result_for_raw_data = ref([]);
    const axios_query_raw_data = async (check_which_country, check_which_url) => {
      let check_which_url_after_replace = check_which_url.replace("https://", "").replace("http://", "")
      let url_to_get_for_checking_raw_data = `http://localhost:5030/d02_show_raw_data/${check_which_country}/${check_which_url_after_replace}`
      console.log(`url_to_get_for_checking_raw_data=${url_to_get_for_checking_raw_data}`)
      let response = await axios.get(url_to_get_for_checking_raw_data);
      list_result_for_raw_data.value = response.data;
      console.log(list_result_for_raw_data)
    };

    const columns_for_raw_data = [
      {
        name: "country",
        required: true,
        label: "country",
        align: "left",
        field: (row) => row.country,
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


    };
  },
};
</script>
