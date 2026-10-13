<template>
<div :key="componentId">
    <q-btn color="primary" @click="b01_show_child_component_or_hide_it()">{{availiblity}} </q-btn>
</div>
</template>

<script>
import axios from "axios";
import {
  ref,
  reactive
} from "vue";
export default {
  props: {
    some_country: String,
    some_url: String,
    availiblity: String,
  },
  emits: ['toggle-expansion'],
  setup(props, { emit }) {
    const componentId = `${props.some_country}_${props.some_url.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const show_or_hide_the_child_component_table = ref("dont_show_child_compoennt_table");

    function b01_show_child_component_or_hide_it() {
      if (show_or_hide_the_child_component_table.value === "dont_show_child_compoennt_table") {
        show_or_hide_the_child_component_table.value = "show_child_component_table"
      } else if (show_or_hide_the_child_component_table.value === "show_child_component_table") {
        show_or_hide_the_child_component_table.value = "dont_show_child_compoennt_table"
      }
      
      // Emit the toggle event to parent with the component's data
      emit('toggle-expansion', {
        country: props.some_country,
        url: props.some_url,
        isExpanded: show_or_hide_the_child_component_table.value === "show_child_component_table",
        componentId: componentId
      });
    }

    // -------------------------------------
    const check_which_country = ref(props.some_country)
    const check_which_url_before_replace = ref(props.some_url)
    const availiblity = ref(props.availiblity)
    const list_result_for_raw_data = ref([]);
    const axios_query_raw_data = async () => {
      let check_which_url_after_replace = check_which_url_before_replace.value.replace("https://", "").replace("http://", "")
      let url_to_get_for_checking_raw_data = `http://localhost:5030/d02_show_raw_data/${check_which_country.value}/${check_which_url_after_replace}`
      let response = await axios.get(url_to_get_for_checking_raw_data);
      list_result_for_raw_data.value = response.data;
    };
    axios_query_raw_data()

    const columns_for_raw_data = [{
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
      field: (row) => row.probe_ip,
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

    const pagination_for_raw_data = ref({
      sortBy: 'desc',
      descending: false,
      rowsPerPage: 100
    })
    return {
      pagination_for_raw_data,
      columns_for_raw_data,
      list_result_for_raw_data,
      b01_show_child_component_or_hide_it,
      show_or_hide_the_child_component_table,
      check_which_country,
      check_which_url_before_replace,
      componentId
    }
  }
}
</script>


<style lang="scss" scoped>
.q-table .q-table__cell--curl_result_link{
  width: 10px;
}

</style>