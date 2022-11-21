import { createApp } from 'vue'
import FilingUploader from "./FilingUploader.vue"

const app = createApp({});
app.component("FilingUploader", FilingUploader);
app.mount("#vue-app");
