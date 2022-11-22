<template>
  <div>
    <h5 class="uploader-label" :class="{ 'has-optional': formDef.optional }">
      {{ formDef.preText }}
      <span :id="'Tooltip-' + uniqueId" class="popover-link">
        <span class="content">
        {{ formDef.name }}
        </span>
        <i class="fa fa-question-circle"></i>
      </span>
      <span v-if="formDef.postText"> {{ formDef.postText }}</span>
      <span v-else-if="party === 1"> for You</span>
      <span v-else-if="party === 2"> for Your Spouse</span>
      <span v-else-if="party === 0 && formDef.indicateWhenJoint"> - Joint</span>
    </h5>
    <p v-if="formDef.optional">
      (<strong>Optional</strong>: {{ formDef.optional }})
    </p>
    <popover
      :title="formDef.name"
      trigger="outside-click"
      :target="'#Tooltip-' + uniqueId"
      placement="right"
      :auto-placement="true"
    >
      <template #popover>
        <p>{{ formDef.help }}</p>
        <br>
        <p>{{ formDef.signature }}</p>
      </template>
    </popover>
    <label :for="inputId" class="sr-only">
      {{ formDef.preText }} {{ formDef.name }}
      <span v-if="party === 1"> - For You</span>
      <span v-if="party === 2"> - For Your Spouse</span>
    </label>
    <div
      @dragover="dragOn"
      @dragenter="dragOn"
      @dragleave="dragOff"
      @dragend="dragOff"
      @drop="dragOff"
    >
      <file-upload
        ref="upload"
        v-model="files"
        :multiple="true"
        :maximum="maxFiles"
        :size="maxMegabytes * 1024 * 1024"
        :drop="true"
        :drop-directory="false"
        :post-action="postAction"
        :input-id="inputId"
        name="file"
        :headers="{ 'X-CSRFToken': getCSRFToken() }"
        :class="['drop-zone', dragging ? 'dragging' : '']"
        :data="inputKeys"
        @input-file="inputFile"
        @input-filter="inputFilter"
      >
        <div
          v-if="files.length === 0"
          class="placeholder"
          :class="{ 'required': !formDef.optional }"
        >
          <i class="fa fa-plus-circle"></i><br />
          <em>
            Drag and Drop the PDF document or JPG pages here,<br />or click here
            to Browse for files.
          </em>
        </div>
        <template v-else>
          <div v-if="fileErrors === 1" class="text-danger error-top">
            <strong>
              One file has failed to upload to the server. Please remove the
              file marked 'File Upload Error' and try uploading it again.
            </strong>
          </div>
          <div v-if="fileErrors > 1" class="text-danger error-top">
            <strong>
              Some files have failed to upload to the server. Please remove the
              files marked 'File Upload Error' and try uploading them again.
            </strong>
          </div>
          <div v-if="tooBig" class="text-danger error-top">
            <strong>
              The total of all uploaded files for this form cannot exceed
              {{ maxMegabytes }} MB. Please reduce the size of your files so the
              total is below this limit.
            </strong>
          </div>
          <div class="cards">
            <div v-for="(file, index) in files" :key="index" class="card">
              <item-tile
                :file="file"
                :index="index"
                :file-count="files.length"
                @remove="remove(file)"
                @moveup="moveUp(index)"
                @movedown="moveDown(index)"
                @rotateleft="rotateLeft(index)"
                @rotateright="rotateRight(index)"
              />
            </div>
            <div v-if="!tooBig" class="upload-button">
              <div class="upload-button-wrapper">
                <i class="fa fa-plus-circle"></i>
              </div>
            </div>
          </div>
          <div v-if="tooBig" class="text-danger pull-right error-bottom">
            <em>
              <strong>
                (Total
                {{ Math.round((totalSize / 1024 / 1024) * 100) / 100 }} MB of
                {{ maxMegabytes }} MB)
              </strong>
            </em>
          </div>
        </template>
      </file-upload>
    </div>
    <div v-if="!tooBig" class="text-right">
      <em>(Maximum {{ maxMegabytes }} MB)</em>
    </div>

    <modal ref="warningModal" v-model="showWarning" class="warning-modal">
      {{ warningText }}
    </modal>
  </div>
</template>

<script>
  import VueUploadComponent from "vue-upload-component";
  import { Modal, Popover } from "uiv";
  import axios from "axios";
  import Compressor from "compressorjs";
  import ItemTile from "./ItemTile.vue";
  import FormDefinitions from "../../utils/forms";
  import rotateFix from "../../utils/rotation";

  export default {
    name: "FileUploader",
    components: {
      FileUpload: VueUploadComponent,
      ItemTile,
      Modal,
      Popover
    },
    inject: ['proxyRootPath'],
    props: {
      docType: {
        type: String,
        required: true
      },
      party: {
        type: Number,
        default: 0
      },
      filingType: {
        type: String,
        required: true
      }
    },
    data() {
      return {
        maxFiles: 30,
        maxMegabytes: 10,
        files: [],
        dragging: false,
        showWarning: false,
        warningText: "",
        isDirty: false,
        retries: 0,
      };
    },
    computed: {
      inputId() {
        return `Uploader-${ this.uniqueId }`;
      },
      inputKeys() {
        return {
          doc_type: this.docType,
          party_code: this.party,
          filing_type: this.filingType,
        };
      },
      formDef() {
        return FormDefinitions[this.docType];
      },
      postAction() {
        return `${this.proxyRootPath }api/documents/`;
      },
      uniqueId() {
        if (this.party === 0) {
          return this.docType;
        }
        return this.docType + this.party;
      },
      totalSize() {
        let size = 0;
        this.files.forEach((file) => {
          if (!file.error) {
            size += file.size;
          }
        });
        return size;
      },
      fileErrors() {
        let count = 0;
        this.files.forEach((file) => {
          if (file.error) {
            count += 1;
          }
        });
        return count;
      },
      tooBig() {
        return this.totalSize > this.maxMegabytes * 1024 * 1024;
      },
    },
    created() {
      // get saved state from the server
      const url = `${this.proxyRootPath}api/graphql/`;
      axios
        .post(url, {
          query: `
        query getMetadata {
          documents(docType:"${this.docType}",partyCode:${this.party}) {
            filename size width height rotation contentType
          }
        }
      `,
          variables: null,
        })
        .then((response) => {
          response.data.data.documents.forEach((doc) => {
            this.files.push({
              name: doc.filename,
              size: doc.size,
              width: doc.width,
              height: doc.height,
              rotation: doc.rotation,
              type: doc.contentType,
              error: false,
              success: true,
              progress: "100.00",
              // we add an extra 'x' to the file extension so the siteminder proxy doesn't treat it as an image
              objectURL: `${this.proxyRootPath}api/documents/${this.docType}/${this.party}/${doc.filename}x/${doc.size}/`,
            });
          });
        })
        .catch((error) => {
          this.showError("Error getting metadata");
          console.error("error", error);
        });

      // call the API to update the metadata every second, but only if
      // the data has changed (throttling requests because rotating and
      // re-ordering images can cause a lot of traffic and possibly
      // result in out-of-order requests)
      setInterval(() => {
        if (this.isDirty && this.retries < 15) {
          this.saveMetaData();
          this.isDirty = false;
        }
      }, 1000);

      // Prevent browser from loading a drag-and-dropped file if it's
      // not dropped in the correct area
      window.addEventListener(
      "dragover",
      e => {
        if (e.currentTarget) e.preventDefault();
      },
      false
      );
      window.addEventListener(
        "drop",
        e => {
          e.preventDefault();
        },
        false
      );
    },
    methods: {
      inputFile(newFile, oldFile) {
        // upload is complete
        if (newFile && oldFile && !newFile.active && oldFile.active) {
          if (newFile.xhr) {
            //  Error Handling
            const statusCode = newFile.xhr.status;
            if (statusCode === 400) {
              // 400 validation error: show the message returned by the server
              let message = newFile.xhr.responseText;
              const response = JSON.parse(message);
              if (response.file) {
                [ message ] = response.file;
              }
              this.showError(message);
              this.$refs.upload.remove(newFile);
            } else if (statusCode === 403) {
              this.showError(
                "Error: Your user session has expired. Please log in again."
              );
            } else if (statusCode !== 200 && statusCode !== 201) {
              // 500 server error: show the status text and a generic message
              this.showError(
                `Error: ${newFile.xhr.statusText}. Please try the upload again. If this doesn't work, try again later.`
              );
              console.log("status", statusCode);
            }
          }
        }

        // Automatically activate upload after compression completes
        if (newFile && newFile.compressed && !newFile.active) {
          newFile.active = true;
        }
      },
      inputFilter(newFile, oldFile, prevent) {
        if (newFile && !oldFile) {
          // Filter non-image file
          if (!/\.(jpeg|jpg|gif|png|pdf)$/i.test(newFile.name)) {
            this.showError(
              "Unsupported file type.  Allowed file types are .jpeg, .jpg, .gif, .png and .pdf."
            );
            return prevent();
          }

          this.files.forEach((file) => {
            // prevent duplicates (based on filename and length)
            if (file.name === newFile.name && file.length === newFile.length) {
              this.showError(
                `This file appears to have already been uploaded for this document. Duplicate filename: ${newFile.name}`
              );
              return prevent();
            }
          });

          // Automatic compression
          const self = this;
          if (newFile.file && newFile.type.substr(0, 6) === "image/") {
            new Compressor(newFile.file, {
              quality: 0.8,
              maxWidth: 2100,
              maxHeight: 2100,
              convertSize: Infinity,
              success(result) {
                self.$refs.upload.update(newFile, {
                  error: false,
                  file: result,
                  size: result.size,
                  type: result.type,
                  compressed: true,
                });
              },
              error(err) {
                console.error(err);
                self.$refs.upload.update(newFile, {
                  error: "compression failed",
                });
              },
            });
          } else {
            newFile.compressed = true;
          }
        }

        if (newFile) {
          // make sure the user isn't uploading more MB of files than allowed
          if (this.totalSize > this.maxMegabytes * 1024 * 1024) {
            this.showError(
              `The total of all uploaded files for this form cannot exceed ${this.maxMegabytes} MB. Please reduce the size of your files so the total is below this limit.`
            );

            // only allow one file over the limit (so we can show the red messaging on the screen)
            let previousTotalSize = 0;
            this.files.forEach((file) => {
              if (file.name !== newFile.name && !file.error) {
                previousTotalSize += file.size;
              }
            });

            // if the user is more than one file over the limit, then block the upload
            if (previousTotalSize > this.maxMegabytes * 1024 * 1024) {
              this.$refs.upload.remove(newFile);
              return prevent();
            }
          }

          // if it's a PDF, make sure it's the only item being uploaded
          if (newFile.type === "application/pdf") {
            if (this.files.length > 0) {
              if (
                this.files[0].name !== newFile.name ||
                this.files[0].length !== newFile.length
              ) {
                this.showError(
                  "Only one PDF is allowed per form, and PDF documents cannot be combined with images."
                );
                this.$refs.upload.remove(newFile);
                return prevent();
              }
            }
          } else {
            // if it's not a PDF, make sure there are no PDFs already uplaoded
            this.files.forEach((file) => {
              if (file.type === "application/pdf") {
                this.showError(
                  "PDF documents cannot be combined with images. Only a single PDF or multiple images can be uploaded into one form. "
                );
                this.$refs.upload.remove(newFile);
                return prevent();
              }
            });
          }
          // Add extra data to the file object
          newFile.objectURL = "";
          newFile.width = 0;
          newFile.height = 0;
          newFile.rotation = 0;
          const URL = window.URL || window.webkitURL;
          if (URL && URL.createObjectURL) {
            newFile.objectURL = URL.createObjectURL(newFile.file);
            const img = new Image();
            const self = this;
            img.onload = () => {
              newFile.width = this.width || 0;
              newFile.height = this.height || 0;
              self.isDirty = true;
            };
            img.src = newFile.objectURL;
          }
        }
      },
      remove(file) {
        const urlbase = `${this.proxyRootPath}api/documents`;
        const encFilename = encodeURIComponent(file.name);
        const token = this.getCSRFToken();
        if (!file.error) {
          // we add an extra 'x' to the file extension so the siteminder proxy doesn't treat it as an image
          const url = `${urlbase}/${this.docType}/${this.party}/${encFilename}x/${file.size}/`;
          axios
            .delete(url, { headers: { "X-CSRFToken": token } })
            .then(() => {
              const pos = this.files.findIndex(
                (f) => f.docType === file.docType && f.size === file.size
              );
              if (pos > -1) {
                this.files.splice(pos, 1);
              }
            })
            .catch(() => {
              this.showError(
                `Error deleting document from the server: ${ file.name}`
              );
              this.$refs.upload.remove(file);
            });
        } else {
          this.$refs.upload.remove(file);
        }
      },
      moveUp(oldIndex) {
        if (oldIndex >= 1 && this.files.length > 1) {
          this.files.splice(
            oldIndex - 1,
            0,
            this.files.splice(oldIndex, 1)[0]
          );
        }
        this.isDirty = true;
      },
      moveDown(oldIndex) {
        if (oldIndex <= this.files.length && this.files.length > 1) {
          this.files.splice(
            oldIndex + 1,
            0,
            this.files.splice(oldIndex, 1)[0]
          );
        }
        this.isDirty = true;
      },
      rotateLeft(index) {
        this.files[index].rotation -= 90;
        this.isDirty = true;
      },
      rotateRight(index) {
        this.files[index].rotation += 90;
        this.isDirty = true;
      },
      dragOn() {
        this.dragging = true;
      },
      dragOff() {
        this.dragging = false;
      },
      showError(message) {
        this.warningText = message;
        this.showWarning = true;
      },
      saveMetaData() {
        const allFiles = [];
        this.files.forEach((file) => {
          if (!file.error) {
            allFiles.push({
              filename: file.name,
              size: file.size,
              width: file.width,
              height: file.height,
              rotation: rotateFix(file.rotation),
            });
          }
        });
        const data = {
          docType: this.docType,
          partyCode: this.party,
          files: allFiles,
        };
        const json = JSON.stringify(data);
        const graphQLData = json.replace(/"([^"]+)":/g, '$1:');
        const url = `${this.proxyRootPath}api/graphql/`;
        axios
          .post(url, {
            query: `
          mutation updateMetadata {
            updateMetadata(input:${graphQLData}){
              documents{filename size width height rotation contentType}
            }
          }
        `,
          })
          .then((response) => {
            // check for errors in the graphQL response
            this.retries = 0;
            if (response.data.errors && response.data.errors.length) {
              response.data.errors.forEach((error) => {
                console.error("error", error.message || error);
                // if there was an error it's probably because the upload isn't finished yet
                // mark the metadata as dirty, so it will save metadata again
                this.retries += 1;
                this.isDirty = true;
              });
            }
          })
          .catch((error) => {
            this.showError("Error saving metadata");
            console.error("error", error);
          });
      },
      getCSRFToken() {
        const name = "csrftoken";
        if (document.cookie && document.cookie !== "") {
          const cookies = document.cookie.split(";");
          for (let i = 0; i < cookies.length; i += 1) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === `${ name }=`) {
              return decodeURIComponent(cookie.substring(name.length + 1));
            }
          }
        }
        return null;
      }
    },
  };
</script>

<style scoped lang="scss">
  .drop-zone {
    background-color: white;
    width: 100%;
    display: block;
    text-align: left;
    border: 1px #365ebe dashed;
    border-radius: 8px;
    padding: 20px 32px 0 20px;
    margin-bottom: 5px;

    &.dragging {
      background-color: #d7dff2;
    }

    .cards {
      display: flex;
      flex-wrap: wrap;
      justify-content: left;
    }

    .card {
      flex: 0 1 160px;
      margin-bottom: 10px;
      width: 160px;
      margin-right: 18px;
    }

    .upload-button {
      position: absolute;
      right: 16px;
      top: 17px;
    }

    .fa-plus-circle {
      font-size: 30px;
      margin-bottom: 8px;
      color: #365ebe;
    }

    .placeholder {
      text-align: center;
      margin-bottom: 18px;
    }

    .error-top {
      padding-bottom: 16px;
    }

    .error-bottom {
      margin-bottom: 8px;
    }
  }

  h5.uploader-label {
    display: block;
    margin-top: 20px;
    margin-bottom: 20px;
    font-weight: normal;
    font-size: 21px;

    &.has-optional {
      margin-bottom: 0;
    }

    span.popover-link {
      color: #365ebe;
      font-weight: bold;
    }
  }
</style>

<style type="css">
  /* hide the cancel button on the warning modal */
  .warning-modal button.btn-default {
    display: none;
  }

  .warning-modal button.btn-primary {
    min-width: 80px;
  }

  /* override vue-upload-component styles for IE11 issues */
  .file-uploads-html5 input[type="file"] {
    height: 0 !important;
    padding: 0 !important;
    border: none !important;
  }

  .file-uploads-html5 label {
    display: inline;
  }
</style>
