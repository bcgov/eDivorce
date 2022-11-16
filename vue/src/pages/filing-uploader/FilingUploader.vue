<template>
  <div id="app">
    <div v-for="(item, index) in formTypes" :key="index">
      <file-uploader
        :doc-type="item.doc_type"
        :party="item.party_code"
        :filing-type="filingType"
      />
    </div>
  </div>
</template>

<script>
  import FileUploader from "../../components/Uploader/Uploader.vue";

  export default {
    name: "FilingUploader",
    components: {
      FileUploader,
    },
    provide() {
      return {
        proxyRootPath: this.proxyRootPath
      }
    },
    props: {
      formTypes: {
        type: Array,
        required: true
      },
      filingType: {
        type: String,
        default: ""
      },
      proxyRootPath: {
        type: String,
        required: true
      },
    },
  };
</script>
