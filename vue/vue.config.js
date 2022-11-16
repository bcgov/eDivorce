module.exports = {
  outputDir: '../edivorce/apps/core/static/dist/vue',
  filenameHashing: false,
  runtimeCompiler: true,
  pages: {
    filingUploader: {
      entry: 'src/pages/filing-uploader/main.js',
      template: 'public/filing-uploader.html',
      filename: 'index.html',
      chunks: ['chunk-vendors', 'chunk-common', 'filingUploader']
    }
  },
  chainWebpack: config => {
    if (process.env.NODE_ENV !== "production") {
        config.devtool('source-map')
    }
    config.module
      .rule('vue')
      .use('vue-loader')
      .loader('vue-loader')
      .tap(options => ({
          ...options,
          compilerOptions: {
            whitespace: "preserve"
          },
          optimization: {
            splitChunks: {
              minSize: 1
            }
          }
        }))
  },
  css: {
    extract: true
  },
  lintOnSave: false
}
