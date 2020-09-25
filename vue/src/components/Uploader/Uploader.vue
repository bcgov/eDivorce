<template>
<div>
  <h5 class="uploader-label">
    {{ formDef.preText }} 
    <a href="javascript:void(0)" :id="'Tooltip-' + uniqueId">
      {{ formDef.name }} <i class="fa fa-question-circle"></i>
    </a>
    <strong v-if="party === 1"> - For You</strong>
    <strong v-if="party === 2"> - For Your Spouse</strong>
  </h5>  
  <tooltip :text="formDef.help" :target="'#Tooltip-' + uniqueId"></tooltip>
  <label :for="inputId" class="sr-only">
    {{ formDef.preText }} {{ formDef.name }} 
    <span v-if="party === 1"> - For You</span>
    <span v-if="party === 2"> - For Your Spouse</span>
  </label>
  <div @dragover="dragOn" @dragenter="dragOn" @dragleave="dragOff" @dragend="dragOff" @drop="dragOff">
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
      :class="['drop-zone', dragging ? 'dragging' : '']"
      :data="inputKeys"
      @input-file="inputFile"
      @input-filter="inputFilter">
    <div v-if="files.length === 0" class="placeholder">
      <i class="fa fa-plus-circle"></i><br>
      <em>Drag and Drop the PDF document or JPG pages here,<br>or click here to Browse for files.</em>
    </div>
    <template v-else>
      <div class="text-danger error-top" v-if="fileErrors === 1">
        <strong>One file has failed to upload to the server. Please remove the file marked 'File Upload Error' and try uploading it again.</strong>
      </div>
      <div class="text-danger error-top" v-if="fileErrors > 1">
        <strong>Some files have failed to upload to the server. Please remove the files marked 'File Upload Error' and try uploading them again.</strong>
      </div>      
      <div class="text-danger error-top" v-if="tooBig">
        <strong>The total of all uploaded files for this form cannot exceed {{ maxMegabytes }} MB.
        Please reduce the size of your files so the total is below this limit.</strong>
      </div>
      <div class="cards">
        <div v-for="(file, index) in files" v-bind:key="index" class="card">
          <item-tile
            :file="file"
            :index="index"
            :file-count="files.length"
            @remove="remove(file)"
            @moveup="moveUp(index)"
            @movedown="moveDown(index)"
            @rotateleft="rotateLeft(index)"
            @rotateright="rotateRight(index)"/>
        </div>
        <div class="card upload-button" v-if="!tooBig">
          <div class="upload-button-wrapper">
          <i class="fa fa-plus-circle"></i>
          </div>
        </div>
      </div>
      <div class="text-danger pull-right error-bottom" v-if="tooBig">
        <em>
          <strong>
            (Total {{ Math.round(totalSize/1024/1024 * 100) / 100 }} 
            MB of {{ maxMegabytes }} MB)
          </strong>
        </em>
      </div>      
    </template>
    </file-upload>
  </div>
  <div class="pull-right" v-if="!tooBig">
    <em>(Maximum {{ maxMegabytes }} MB)</em>
  </div>
  <modal ref="warningModal" class="warning-modal" v-model="showWarning">
    {{ warningText }}
  </modal>
</div>
</template>

<script>
import VueUploadComponent from 'vue-upload-component'
import { Tooltip, Modal } from 'uiv';
import ItemTile from './ItemTile'
import FormDefinitions from "../../utils/forms";
import rotateFix from '../../utils/rotation';

export default {
  props: {
    docType: String,
    party: { type: Number, default: 0 }
  },
  data: function () {
    return {
      maxFiles: 30,
      maxMegabytes: 10,
      files: [],
      dragging: false,
      showWarning: false,
      warningText: "",
      isDirty: false
    }
  },
  components: {
    FileUpload: VueUploadComponent,
    ItemTile,
    Tooltip,
    Modal
  },
  computed: {
    inputId() {
      return "Uploader-" + this.uniqueId;
    },
    inputKeys() {
      return {
        doc_type: this.docType,
        party_code: this.party
      };
    },    
    formDef() {
      return FormDefinitions[this.docType];
    },
    postAction() {
      return this.$parent.proxyRootPath + "api/documents/"
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
          count++;
        }
      });
      return count;
    },    
    tooBig() {
      return this.totalSize > this.maxMegabytes * 1024 * 1024;
    }
  },
  methods: {
    inputFile(newFile, oldFile) {

      // upload is complete
      if (newFile && oldFile && !newFile.active && oldFile.active) {

        // todo: send metadata to the server 
        console.log('Upload Complete; file=' + newFile.name)
        this.saveMetaData();

        if (newFile.xhr) {
          //  Get the response status code (we can use this for error handling)
          if (newFile.xhr.status !== 200) {
            // todo: handler errors
            this.showError('Error: ' + newFile.xhr.statusText + '. Please try the upload again. If this doesn\'t work, try again later.');
            console.log('status', newFile.xhr.status)
          }
        }
      }
      this.$refs.upload.active = true;
    },
    inputFilter(newFile, oldFile, prevent) {
      if (newFile && !oldFile) {
        // Filter non-image file
        if (!/\.(jpeg|jpg|gif|png|pdf)$/i.test(newFile.name)) {
          this.showError('Unsupported file type.  Allowed file types are .jpeg, .jpg, .gif, .png and .pdf.');
          return prevent()
        }

        this.files.forEach((file) => {
          // prevent duplicates (based on filename and length)
          if (file.name === newFile.name && file.length === newFile.length) {
            this.showError('This file appears to have already been uploaded with for this document. Duplicate filename: ' + newFile.name);
            return prevent();
          }
        });
      }

      if (newFile) {
        // make sure the user isn't uploading more MB of files than allowed
        if (this.totalSize > this.maxMegabytes * 1024 * 1024) {
          this.showError('The total of all uploaded files for this form cannot exceed ' + this.maxMegabytes + ' MB. Please reduce the size of your files so the total is below this limit.');

          // only allow one file over the limit (so we can show the red messaging on the screen)
          let previousTotalSize = 0;
          this.files.forEach((file) => {
            if ((file.name !== newFile.name || file.size !== newFile.size) && !file.error) {
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
        if (newFile.type === 'application/pdf') {
          if (this.files.length > 0) {
            if (this.files[0].name != newFile.name || this.files[0].length != newFile.length) {
              this.showError('Only one PDF is allowed per form, and PDF documents cannot be combined with images.');
              this.$refs.upload.remove(newFile);
              return prevent();
            }
          }

        } else {
          // if it's not a PDF, make sure there are no PDFs already uplaoded
          this.files.forEach((file) => {
            if (file.type === 'application/pdf') {
              this.showError('PDF documents cannot be combined with images. Only a single PDF or multiple images can be uploaded into one form. ');
              this.$refs.upload.remove(newFile);
              return prevent();
            }
          });
        }

        // Add extra data to to the file object
        newFile.objectURL = ''
        let URL = window.URL || window.webkitURL
        if (URL && URL.createObjectURL) {
          newFile.objectURL = URL.createObjectURL(newFile.file)
          newFile.rotation = 0;
          const img = new Image();
          img.onload = function() {
            newFile.width = this.width;
            newFile.height = this.height;
          }
          img.src = newFile.objectURL;
        }
      }
    },
    remove(file) {
      // todo: call the API to remove the file
      this.$refs.upload.remove(file)
    },
    moveUp(old_index) {
      if (old_index >= 1 && this.files.length > 1) {
        this.files.splice(old_index - 1, 0, this.files.splice(old_index, 1)[0]);
      }
      this.isDirty = true;
    },
    moveDown(old_index) {
      if (old_index <= this.files.length && this.files.length > 1) {
        this.files.splice(old_index + 1, 0, this.files.splice(old_index, 1)[0]);
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
      let allFiles = [];
      this.files.forEach((file) => {
        allFiles.push({
          filename: file.name, 
          size: file.size, 
          rotation: rotateFix(file.rotation)
        });
      });
      const data = {
        docType: this.docType,
        partyCode: this.party,
        files: allFiles
      };
      console.log('Call API', data);
    }
  },
  created() {
    // call the API to update the metadata every second, but only if
    // the data has changed (throttling requests because rotating and
    //  re-ordering images can cause a lot of traffic)
    setInterval(() => {
      if (this.isDirty) {
        this.saveMetaData();
        this.isDirty = false;
      }
    }, 1000);

    // Prevent browser from loading a drag-and-dropped file if it's
    // not dropped in the correct area
    window.addEventListener("dragover",function(e){
    e = e || event;
    e.preventDefault();
    },false);

    window.addEventListener("drop",function(e){
    e = e || event;
    e.preventDefault();
    },false);    
  }
}
</script>

<style scoped lang="scss">
  .drop-zone {
    background-color: white;
    width: 100%;
    display: block;
    text-align: left;
    border: 2px #365EBE dashed;
    border-radius: 6px;
    padding: 18px;

    &.dragging {
      background-color: #F2E3F2;
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

      &.upload-button {
        display: flex;
        flex-direction: column;
        justify-content: center;
      }
    }

    .fa-plus-circle {
      font-size: 3rem;
      margin-bottom: 8px;
      color: #365EBE;
    }

    .placeholder {
      text-align: center;
    }

    .error-top {
      padding-bottom: 16px;
    }

    .error-bottom {
      margin-bottom: -10px;
    }
  }

  h5.uploader-label {
    display: block;   
    margin-top: 30px;
    margin-bottom: 10px;
    font-weight: normal;
    font-size: 1em;

    a {
      font-weight: bold;
      text-decoration: underline;
    }
  }
</style>

<style type="css">
  /* hide the cancel button on the warnig modal */
  .warning-modal button.btn-default {
    display: none;
  }

  .warning-modal button.btn-primary {
    min-width: 80px;
  }

  /* override vue-upload-component styles for IE11 issues */
  .file-uploads-html5 input[type=file] {
    height: 0 !important;
    padding: 0 !important;
    border: none !important;
  }

  .file-uploads-html5 label {
    display: inline;
  }
</style>