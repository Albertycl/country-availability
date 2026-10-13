<template>
<div class="q-pt-lg">
    <!-- show_the_button_and_table -->
    <div class="col">
        <q-table style="height: 100%" title="Real-time Domain Testing Progress - Probe Discovery → Curl Testing → Availability Calculation" class="my-sticky-header-column-table " :rows="list_url_query_status" :columns="columns_for_avaiability" row-key="name" virtual-scroll >
            <template v-slot:body-cell-has_the_url_been_checked="props">
                <q-td>
                    <!-- Haven't been checked -->
                    <div class="text-red-7" v-if="props.row.has_the_url_been_checked === 'havent_been_checked'">
                        <q-icon name="pending" size="sm" class="q-mr-sm" />
                        <span class="text-weight-medium">Pending</span>
                    </div>

                    <!-- In process of checking -->
                    <div class="text-orange-8" v-else-if="props.row.has_the_url_been_checked === 'in_process_of_checking_this_url'">
                        <div class="q-mb-xs">
                            <q-spinner-dots color="orange" size="1.5em" class="q-mr-sm" />
                            <span class="text-weight-medium">{{ getDetailedStatus(props.row) }}</span>
                        </div>
                        <div class="text-caption text-grey-7">
                            Elapsed: {{ getElapsedTime(props.row) }}
                        </div>
                        <q-linear-progress
                            :value="getProgressValue(props.row)"
                            color="orange"
                            size="3px"
                            class="q-mt-xs"
                        />
                    </div>

                    <!-- Finished checking -->
                    <div class="text-green-7" v-else-if="props.row.has_the_url_been_checked === 'finish_checking_this_url'">
                        <q-icon name="check_circle" size="sm" class="q-mr-sm" />
                        <span class="text-weight-medium">Completed</span>
                    </div>

                    <!-- Calculating availability -->
                    <div class="text-blue-7" v-else-if="props.row.has_the_url_been_checked === 'calculating_availability'">
                        <q-spinner-hourglass color="blue" size="1.5em" class="q-mr-sm" />
                        <span class="text-weight-medium">Calculating Availability</span>
                    </div>

                    <!-- Default fallback -->
                    <div class="text-grey-6" v-else>
                        <q-icon name="help" size="sm" class="q-mr-sm" />
                        <span>{{ props.row.has_the_url_been_checked }}</span>
                    </div>
                </q-td>
            </template>
        </q-table>

    </div>
</div>
</template>

<script>
import {
  ref
} from "vue";
import axios from "axios";
export default {
  name: "table_for_showing_which_domain_is_being_query_at_the_moment",
  props: {
    show_the_button_and_table: String,
  },
  setup(props) {
    const list_url_query_status = ref([])

    const url_check_which_domain_is_being_queried_at_the_moment = ref("http://localhost:5030/a20_which_url_is_being_handled");
    const c01_check_which_domain_is_being_queried_at_the_moment = async () => {
      try {
        await axios.get(url_check_which_domain_is_being_queried_at_the_moment.value).then((response) => (list_url_query_status.value = response.data));

      } catch (error) {
        throw Error("no data available");
      }
    };
    c01_check_which_domain_is_being_queried_at_the_moment()
    const columns_for_avaiability = [
      {
        name: "url_from_jenney_excel",
        required: true,
        label: "url_from_jenney_excel",
        align: "left",
        field: (row) => row.url_from_jenney_excel,
        sortable: true,
      },
      {
        name: "has_the_url_been_checked",
        required: true,
        label: "has_the_url_been_checked",
        align: "left",
        field: (row) => row.has_the_url_been_checked,
        sortable: true,
      },
      {
        name: "start_query_time",
        required: true,
        label: "start_query_time",
        align: "left",
        field: (row) => row.start_query_time,
        sortable: true,
      },
      {
        name: "end_query_time",
        required: true,
        label: "end_query_time",
        align: "left",
        field: (row) => row.end_query_time,
        sortable: true,
      },



    ];

    setInterval(() => {
      if (props.show_the_button_and_table === "hide_the_button_and_table") {
        c01_check_which_domain_is_being_queried_at_the_moment();
        console.log("setInterval for checking the query process");
      }
    }, 10000)

    // Function to get detailed status based on row data
    const getDetailedStatus = (row) => {
      const currentTime = new Date();
      const startTime = row.start_query_time ? new Date(row.start_query_time) : null;

      if (!startTime) {
        return "Starting probe discovery...";
      }

      const elapsedMinutes = (currentTime - startTime) / (1000 * 60);

      if (elapsedMinutes < 0.5) {
        return "🔍 Discovering available probes";
      } else if (elapsedMinutes < 1) {
        return "📡 Connecting to probe servers";
      } else if (elapsedMinutes < 3) {
        return "🌐 Running curl tests on probes";
      } else if (elapsedMinutes < 4) {
        return "📊 Collecting response data";
      } else {
        return "⚙️ Processing results";
      }
    };

    // Function to get elapsed time as a readable string
    const getElapsedTime = (row) => {
      const currentTime = new Date();
      const startTime = row.start_query_time ? new Date(row.start_query_time) : null;

      if (!startTime) {
        return "0s";
      }

      const elapsedSeconds = Math.floor((currentTime - startTime) / 1000);

      if (elapsedSeconds < 60) {
        return `${elapsedSeconds}s`;
      } else {
        const minutes = Math.floor(elapsedSeconds / 60);
        const seconds = elapsedSeconds % 60;
        return `${minutes}m ${seconds}s`;
      }
    };

    // Function to calculate progress value (0-1)
    const getProgressValue = (row) => {
      const currentTime = new Date();
      const startTime = row.start_query_time ? new Date(row.start_query_time) : null;

      if (!startTime) {
        return 0;
      }

      const elapsedMinutes = (currentTime - startTime) / (1000 * 60);
      const expectedDuration = 4; // 4 minutes expected duration

      if (elapsedMinutes < 0.5) {
        return 0.1; // 10% - discovering probes
      } else if (elapsedMinutes < 1) {
        return 0.2; // 20% - connecting to probes
      } else if (elapsedMinutes < 3) {
        return 0.2 + (elapsedMinutes - 1) / 2 * 0.6; // 20-80% - curl testing
      } else if (elapsedMinutes < 4) {
        return 0.8 + (elapsedMinutes - 3) * 0.15; // 80-95% - collecting data
      } else {
        return Math.min(0.95 + (elapsedMinutes - 4) * 0.01, 0.99); // 95-99% - processing
      }
    };

    return {
      list_url_query_status,
      columns_for_avaiability,
      getDetailedStatus,
      getElapsedTime,
      getProgressValue
    };
  }
}
</script>
