<template>
<div>
    <a href="#" @click.prevent="toggleDetails" class="text-primary">link</a>
    <div v-if="showDetails" class="q-mt-sm">
        <pre class="curl-result-content">{{curl_result_in_each_probe}}</pre>
    </div>
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
    link: String
  },
  setup(props) {
    const link_passed_from_parent_component = ref(props.link)
    const curl_result_in_each_probe = ref("");
    const showDetails = ref(false);
    
    let link_after_replace = link_passed_from_parent_component.value.replace("http://", "").replace("/", "_")
    
    const axios_query_raw_data = async () => {
      let url_to_query = `http://localhost:5030/open_link/${link_after_replace}`
      // console.log(`url_to_query=${url_to_query}`)
      let response = await axios.get(url_to_query);
      curl_result_in_each_probe.value = response.data;
    };
    
    const toggleDetails = async () => {
      if (!showDetails.value && curl_result_in_each_probe.value === "") {
        // Only fetch data when first opening
        await axios_query_raw_data()
      }
      showDetails.value = !showDetails.value;
    };

    return {
      curl_result_in_each_probe,
      showDetails,
      toggleDetails
    }
  }
}
</script>

<style scoped>
.curl-result-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: break-word;
  max-width: 100%;
  background-color: #f5f5f5;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
}
</style>
